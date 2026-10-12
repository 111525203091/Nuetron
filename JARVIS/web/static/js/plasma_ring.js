/**
 * PlasmaRingWebGL — Pure WebGL Plasma Ring Neural Orb
 * Ported from React/Originkit to standalone pure Vanilla JS WebGL implementation.
 * Features:
 * - Dynamic 3D interactive parametric sphere with wave & FBM deformation
 * - Orbit drag rotation with inertia damping
 * - Cursor hover bulge & proximity reactivity
 * - Speech reactivity (modulates waveHeight, speed, hotspot, and center opacity on voice)
 *
 * Fixed issues:
 * - Use individual gl.uniform3f() per color array element (avoids driver bugs with uniform3fv on arrays)
 * - Use Uint32Array indices via OES_element_index_uint extension to remove 65535 vertex limit
 * - Switch to gl.POINTS rendering for reliable visibility on all drivers
 * - Proper camera direction vector
 */

class PlasmaRingController {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.options = Object.assign({
      colors: ['#FF1744', '#0055FF', '#FF0055', '#7928CA', '#00E5FF'],
      density: 80,
      speed: 70,
      waveHeight: 18,
      centerOpacity: 85,
      scale: 36,
      dragSensitivity: 100,
      tilt: 20,
      radius: 130,
      rimPower: 3.0,
      waveLength: 200,
      waveDirection: 45,
      hoverRadius: 35,
      hoverPush: 85,
      orbitDamping: 50
    }, options);

    // Audio reactivity state
    this.voiceActive = false;
    this.voiceTarget = 0.0;
    this.voiceCurrent = 0.0;

    this.init();
  }

  init() {
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'plasma-ring-canvas';
    this.canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:auto;cursor:grab;border-radius:50%;';
    this.container.innerHTML = '';
    this.container.appendChild(this.canvas);

    const ctxOpts = { alpha: true, antialias: false, premultipliedAlpha: true, depth: false };
    const gl = (
      this.canvas.getContext('webgl2', ctxOpts) ||
      this.canvas.getContext('webgl', ctxOpts) ||
      this.canvas.getContext('experimental-webgl', ctxOpts)
    );

    if (!gl) {
      console.warn('PlasmaRing: WebGL not supported');
      this._fallback();
      return;
    }
    this.gl = gl;

    // Try to enable 32-bit index extension (removes 65535 vertex limit)
    this.ext32 = gl.getExtension('OES_element_index_uint') || null;

    this.DPR_CAP = 1.5;
    this.FOV_DEG = 42;
    this.TAU = Math.PI * 2;
    this.MAX_COLORS = 5;

    if (!this.initShaders()) return;
    this.initBuffers();
    this.initEvents();
    this.startLoop();
  }

  _fallback() {
    // CSS-only glowing orb fallback when WebGL is unavailable
    this.container.style.cssText += `
      border-radius:50%;
      background: radial-gradient(circle at 40% 40%, #ff174488, #0055ff44, #00000000);
      box-shadow: 0 0 60px #ff174466, 0 0 120px #0055ff33;
      animation: plasma-pulse 3s ease-in-out infinite alternate;
    `;
  }

  initShaders() {
    const gl = this.gl;
    const MAX_COLORS = this.MAX_COLORS;

    // Build color uniforms declaration dynamically
    let colorUniforms = '';
    for (let i = 0; i < MAX_COLORS; i++) {
      colorUniforms += `uniform vec3 uColor${i};\n`;
    }

    // Build rampColor using individual uniforms instead of array
    let colorArray = '';
    for (let i = 0; i < MAX_COLORS; i++) {
      colorArray += `colors[${i}] = uColor${i};\n      `;
    }

    const VERT = `
      precision highp float;
      attribute vec2 aPolar;
      attribute float aRnd;

      uniform vec2  uRes;
      uniform float uFocal;
      uniform float uTime;
      uniform float uRadius;
      uniform float uWaveHeight;
      uniform float uWaveLength;
      uniform float uWaveSpeed;
      uniform vec2  uWaveDir;
      uniform float uCamDist;
      uniform float uCamYaw;
      uniform float uCamPitch;
      uniform float uTilt;
      uniform float uRimPower;
      uniform float uCenter;

      uniform float uColorCount;
      ${colorUniforms}
      uniform vec3  uHotspot;
      uniform vec3  uCamDir;

      uniform vec3  uHoverDir;
      uniform float uHoverRadius;
      uniform float uHoverPush;
      uniform float uHoverActive;

      uniform float uPointSize;

      varying vec3  vCol;
      varying float vAlpha;

      vec3 rampColor(float x) {
          vec3 colors[${MAX_COLORS}];
          ${colorArray}
          float p  = clamp(x, 0.0, 1.0) * max(uColorCount - 1.0, 0.0);
          float i0 = floor(p);
          float f  = p - i0;
          vec3 a = colors[0];
          vec3 b = colors[0];
          for (int i = 0; i < ${MAX_COLORS}; i++) {
              if (float(i) == i0)       a = colors[i];
              if (float(i) == i0 + 1.0) b = colors[i];
          }
          return mix(a, b, f);
      }

      void main() {
          float phi   = aPolar.x;
          float theta = aPolar.y;

          float sp  = sin(phi); float cp2 = cos(phi);
          float st  = sin(theta); float ct = cos(theta);

          vec3 norm = vec3(cp2 * ct, sp, cp2 * st);
          vec3 pos  = norm * uRadius;

          float wFreq = 6.2831853 / max(100.0, uWaveLength);
          float proj1 = norm.x * uWaveDir.x + norm.z * uWaveDir.y;
          float proj2 = norm.x * uWaveDir.y - norm.z * uWaveDir.x;

          float ts = uTime * (uWaveSpeed / 120.0);
          float wave1 = sin(proj1 * wFreq * 800.0 + ts * 1.2) * cos(norm.y * wFreq * 600.0 + ts * 0.3);
          float wave2 = sin(proj2 * wFreq * 600.0 + norm.y * 1.5 - ts * 0.5);
          float smoothWave = (wave1 + wave2 * 0.5) * uWaveHeight;
          pos += norm * smoothWave;

          float hFalloff = mix(22.0, 1.5, clamp(uHoverRadius / 100.0, 0.0, 1.0));
          float hDot     = max(0.0, dot(norm, uHoverDir));
          float hEffect  = exp(-(1.0 - hDot) * hFalloff) * uHoverActive;
          float hBulge   = hEffect * uHoverPush;
          pos += norm * hBulge;

          float cy  = cos(uCamYaw); float sy = sin(uCamYaw);
          float tp  = uCamPitch + uTilt;
          float ctp = cos(tp);      float stp = sin(tp);

          float x1  =  pos.x * cy + pos.z * sy;
          float z1  = -pos.x * sy + pos.z * cy;
          float y2  =  pos.y * ctp - z1 * stp;
          float z2  =  pos.y * stp + z1 * ctp;
          float rz  =  uCamDist - z2;

          if (rz < 1.0) {
              gl_Position = vec4(2.0, 2.0, 0.0, 1.0);
              gl_PointSize = 0.0;
              vAlpha = 0.0; vCol = vec3(0.0); return;
          }

          float sx  = x1 * uFocal / rz;
          float sy2 = y2 * uFocal / rz;
          gl_Position  = vec4(sx / (uRes.x * 0.5), sy2 / (uRes.y * 0.5), 0.0, 1.0);

          // Scale point size by depth
          gl_PointSize = uPointSize * (uFocal / rz);

          float rimDot  = abs(dot(norm, uCamDir));
          float fresnel = pow(max(1.0 - rimDot, 0.0), uRimPower);
          fresnel = max(fresnel, uCenter * rimDot);

          float hoverAlpha = hEffect * 0.95;
          float finalAlpha = max(fresnel, hoverAlpha);
          float bri = 0.50 + aRnd * 0.50;

          float t = sp * 0.5 + 0.5;
          vec3 baseCol = rampColor(1.0 - t);
          float polar  = min(pow(abs(sp), 4.0), 1.0);
          vec3 col     = mix(baseCol, uHotspot, polar * 0.88);

          vCol   = col;
          vAlpha = finalAlpha * bri;
      }
    `;

    const FRAG = `
      precision highp float;
      varying vec3  vCol;
      varying float vAlpha;
      void main() {
          // Soft circular point shape
          vec2 uv = gl_PointCoord - 0.5;
          float d = dot(uv, uv);
          if (d > 0.25) discard;
          float soft = 1.0 - smoothstep(0.1, 0.25, d);
          gl_FragColor = vec4(vCol * vAlpha * soft, vAlpha * soft);
      }
    `;

    const compile = (type, src) => {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
        console.error('PlasmaRing Shader Error:', gl.getShaderInfoLog(sh));
        console.error('Source:', src);
        return null;
      }
      return sh;
    };

    const prog = gl.createProgram();
    const vs = compile(gl.VERTEX_SHADER, VERT);
    const fs = compile(gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return false;

    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.error('PlasmaRing Program Link Error:', gl.getProgramInfoLog(prog));
      return false;
    }
    this.prog = prog;

    const U = (name) => gl.getUniformLocation(prog, name);
    this.sA = {
      polar: gl.getAttribLocation(prog, 'aPolar'),
      rnd:   gl.getAttribLocation(prog, 'aRnd')
    };

    // Individual color uniform locations (avoids uColors[i] array driver issues)
    this.colorLocs = [];
    for (let i = 0; i < this.MAX_COLORS; i++) {
      this.colorLocs.push(U(`uColor${i}`));
    }

    this.sU = {
      res: U('uRes'), focal: U('uFocal'),
      time: U('uTime'), radius: U('uRadius'),
      waveHeight: U('uWaveHeight'), waveLength: U('uWaveLength'),
      waveSpeed: U('uWaveSpeed'), waveDir: U('uWaveDir'),
      camDist: U('uCamDist'),
      camYaw: U('uCamYaw'), camPitch: U('uCamPitch'),
      tilt: U('uTilt'), rimPow: U('uRimPower'),
      center: U('uCenter'),
      colorCount: U('uColorCount'),
      hotspot: U('uHotspot'), camDir: U('uCamDir'),
      hoverDir: U('uHoverDir'), hoverRadius: U('uHoverRadius'),
      hoverPush: U('uHoverPush'), hoverActive: U('uHoverActive'),
      pointSize: U('uPointSize')
    };

    return true;
  }

  initBuffers() {
    const gl = this.gl;
    const d = Math.min(120, Math.max(30, this.options.density || 70));
    const TAU = this.TAU;

    // Keep vertex counts safe regardless of uint32 extension
    const N_theta = Math.round(d * 1.4);  // longitude divisions
    const N_phi   = Math.round(d * 0.9);  // latitude divisions
    this.count = N_theta * N_phi;

    console.log(`PlasmaRing: ${N_theta}x${N_phi} = ${this.count} vertices`);

    const polarA = new Float32Array(this.count * 2);
    const rndA   = new Float32Array(this.count);

    let seed = 0xc0ffee7;
    const rnd = () => {
      seed |= 0;
      seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed) ^ seed;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };

    for (let i = 0; i < this.count; i++) {
      const ti = Math.floor(i / N_phi);
      const pi = i % N_phi;
      const theta = (ti + 0.5) / N_theta * TAU;
      const phi   = ((pi + 0.5) / N_phi - 0.5) * Math.PI;
      polarA[i * 2]     = phi;
      polarA[i * 2 + 1] = theta;
      rndA[i]           = rnd();
    }

    this.polarBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.polarBuf);
    gl.bufferData(gl.ARRAY_BUFFER, polarA, gl.STATIC_DRAW);

    this.rndBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.rndBuf);
    gl.bufferData(gl.ARRAY_BUFFER, rndA, gl.STATIC_DRAW);

    gl.disable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    // Additive blending for glowing orb effect
    gl.blendFunc(gl.ONE, gl.ONE);
  }

  parseColor(input) {
    if (!input) return [0, 0, 0];
    let h = input.trim().replace('#', '');
    if (h.length === 3) h = h.split('').map(c => c + c).join('');
    h = h.padEnd(6, '0');
    return [
      parseInt(h.slice(0, 2), 16) / 255,
      parseInt(h.slice(2, 4), 16) / 255,
      parseInt(h.slice(4, 6), 16) / 255
    ];
  }

  initEvents() {
    this.cam = { yaw: 0, pitch: 0, yawV: 0, pitchV: 0 };
    this.drag = { active: false, lastX: 0, lastY: 0 };
    this.hov = { active: 0, target: 0, dirX: 0, dirY: 1, dirZ: 0 };

    const onDown = (e) => {
      this.drag.active = true;
      this.drag.lastX = e.clientX;
      this.drag.lastY = e.clientY;
      this.canvas.style.cursor = 'grabbing';
    };

    const onMove = (e) => {
      const r = this.canvas.getBoundingClientRect();
      const mx = e.clientX - r.left;
      const my = e.clientY - r.top;
      const cx = r.width / 2, cy2 = r.height / 2;
      const nx = (mx - cx) / cx, ny = -(my - cy2) / cy2;
      const len = Math.sqrt(nx * nx + ny * ny + 0.5);
      this.hov.dirX = nx / len;
      this.hov.dirY = ny / len;
      this.hov.dirZ = 0.5 / len;
      this.hov.target = 1;

      if (!this.drag.active) return;
      const dx = e.clientX - this.drag.lastX;
      const dy = e.clientY - this.drag.lastY;
      this.drag.lastX = e.clientX;
      this.drag.lastY = e.clientY;
      const spd = (this.options.dragSensitivity / 100) * (Math.PI / 180);
      this.cam.yawV   += dx * spd;
      this.cam.pitchV += dy * spd;
    };

    const onUp = () => {
      this.drag.active = false;
      this.canvas.style.cursor = 'grab';
    };

    const onLeave = () => { this.hov.target = 0; };

    this.canvas.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    this.canvas.addEventListener('mouseleave', onLeave);

    this.canvas.addEventListener('touchstart', (e) => {
      if (e.touches[0]) onDown(e.touches[0]);
    }, { passive: true });
    window.addEventListener('touchmove', (e) => {
      if (e.touches[0]) onMove(e.touches[0]);
    }, { passive: true });
    window.addEventListener('touchend', onUp);
  }

  setVoiceActivity(active, intensity = 1.0) {
    this.voiceActive = active;
    this.voiceTarget = active ? Math.min(2.0, intensity) : 0.0;
  }

  startLoop() {
    const gl = this.gl;
    let last = performance.now();
    let elapsed = 0;

    const colors = this.options.colors;
    // Pre-parse colors once
    const parsedColors = [];
    for (let i = 0; i < this.MAX_COLORS; i++) {
      parsedColors.push(this.parseColor(colors[Math.min(i, colors.length - 1)]));
    }

    const CAM_FAR = 2100;
    const CAM_PER_SCALE = 15;

    const frame = (now) => {
      this.raf = requestAnimationFrame(frame);
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;
      elapsed += dt;

      // Canvas resize with DPR
      const dpr = Math.min(window.devicePixelRatio || 1, this.DPR_CAP);
      const cw = this.canvas.clientWidth  || this.container.clientWidth  || 260;
      const ch = this.canvas.clientHeight || this.container.clientHeight || 260;
      const w = Math.round(cw * dpr);
      const h = Math.round(ch * dpr);
      if (this.canvas.width !== w || this.canvas.height !== h) {
        this.canvas.width  = w;
        this.canvas.height = h;
        gl.viewport(0, 0, w, h);
      }

      if (w === 0 || h === 0) return; // nothing to draw

      // Smooth voice reactivity
      this.voiceCurrent += (this.voiceTarget - this.voiceCurrent) * 0.12;

      // Camera inertia damping
      const damp = 1 - Math.pow(Math.max(0.01, this.options.orbitDamping / 100), dt * 10);
      this.cam.yaw   += this.cam.yawV;
      this.cam.pitch += this.cam.pitchV;
      this.cam.yawV   *= (1 - damp);
      this.cam.pitchV *= (1 - damp);

      // Idle auto-rotation
      if (!this.drag.active) {
        this.cam.yaw += (0.15 + this.voiceCurrent * 0.45) * dt;
      }

      // Hover lerp
      this.hov.active += (this.hov.target - this.hov.active) * 0.1;

      const focal = h / (2 * Math.tan((this.FOV_DEG / 2) * Math.PI / 180));
      const totalPitch = this.cam.pitch + (this.options.tilt * Math.PI) / 180;

      // Camera direction (view direction = -z in camera space, transformed back to world)
      const cy  = Math.cos(this.cam.yaw), sy = Math.sin(this.cam.yaw);
      const ctp = Math.cos(totalPitch),   stp = Math.sin(totalPitch);
      // Camera looks along +Z in world before rotation; after yaw+pitch it becomes:
      const cdx = sy * ctp;
      const cdy = stp;
      const cdz = cy * ctp;
      const cdl = Math.sqrt(cdx * cdx + cdy * cdy + cdz * cdz) || 1;

      // Reactive params
      const voiceAmp = this.voiceCurrent;
      const dynamicWaveHeight = this.options.waveHeight * (1.0 + voiceAmp * 1.8);
      const dynamicWaveSpeed  = this.options.speed * (1.0 + voiceAmp * 1.5);
      const dynamicCenter     = (this.options.centerOpacity / 100) * (1.0 + voiceAmp * 0.6);

      // Hotspot color
      const [tr, tg, tb] = parsedColors[0];
      const hr = Math.min(1, tr * (0.6 + voiceAmp * 0.4) + 0.8);
      const hg = Math.min(1, tg * 0.4 + 0.7);
      const hb = Math.min(1, tb * 0.5 + 0.8);

      const cameraDistance = CAM_FAR - CAM_PER_SCALE * this.options.scale;
      const timeVal = elapsed * (dynamicWaveSpeed / 50);

      // Point size: scale by canvas size relative to 260px reference, depth adjusted in shader
      const refSize = Math.min(w, h);
      const pointSize = Math.max(1.0, (refSize / 260) * 2.2);

      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(this.prog);
      gl.uniform2f(this.sU.res, w, h);
      gl.uniform1f(this.sU.focal, focal);
      gl.uniform1f(this.sU.time, timeVal);
      gl.uniform1f(this.sU.radius, this.options.radius);
      gl.uniform1f(this.sU.waveHeight, dynamicWaveHeight);
      gl.uniform1f(this.sU.waveLength, this.options.waveLength);
      gl.uniform1f(this.sU.waveSpeed, dynamicWaveSpeed);

      const da = (this.options.waveDirection * Math.PI) / 180;
      gl.uniform2f(this.sU.waveDir, Math.sin(da), Math.cos(da));
      gl.uniform1f(this.sU.camDist, cameraDistance);
      gl.uniform1f(this.sU.camYaw, this.cam.yaw);
      gl.uniform1f(this.sU.camPitch, this.cam.pitch);
      gl.uniform1f(this.sU.tilt, (this.options.tilt * Math.PI) / 180);
      gl.uniform1f(this.sU.rimPow, this.options.rimPower);
      gl.uniform1f(this.sU.center, dynamicCenter);
      gl.uniform1f(this.sU.colorCount, colors.length);
      gl.uniform1f(this.sU.pointSize, pointSize);

      // Set each color uniform individually (avoids uColors[] array driver issues)
      for (let i = 0; i < this.MAX_COLORS; i++) {
        const [r, g, b] = parsedColors[i];
        gl.uniform3f(this.colorLocs[i], r, g, b);
      }

      gl.uniform3f(this.sU.hotspot, hr, hg, hb);
      gl.uniform3f(this.sU.camDir, cdx / cdl, cdy / cdl, cdz / cdl);
      gl.uniform3f(this.sU.hoverDir, this.hov.dirX, this.hov.dirY, this.hov.dirZ);
      gl.uniform1f(this.sU.hoverRadius, this.options.hoverRadius);
      gl.uniform1f(this.sU.hoverPush, this.options.hoverPush);
      gl.uniform1f(this.sU.hoverActive, this.hov.active);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.polarBuf);
      gl.enableVertexAttribArray(this.sA.polar);
      gl.vertexAttribPointer(this.sA.polar, 2, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.rndBuf);
      gl.enableVertexAttribArray(this.sA.rnd);
      gl.vertexAttribPointer(this.sA.rnd, 1, gl.FLOAT, false, 0, 0);

      // Draw as GL_POINTS — each vertex is a glowing dot
      gl.drawArrays(gl.POINTS, 0, this.count);
    };

    this.raf = requestAnimationFrame(frame);
  }

  destroy() {
    if (this.raf) cancelAnimationFrame(this.raf);
    if (this.canvas && this.canvas.parentNode) {
      this.canvas.parentNode.removeChild(this.canvas);
    }
  }
}

window.PlasmaRingController = PlasmaRingController;
