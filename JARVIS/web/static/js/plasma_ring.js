/**
 * PlasmaRingWebGL — Pure WebGL Plasma Ring Neural Orb
 * Ported from React/Originkit to standalone pure Vanilla JS WebGL implementation.
 * Features:
 * - Dynamic 3D interactive parametric sphere with wave & FBM deformation
 * - Orbit drag rotation with inertia damping
 * - Cursor hover bulge & proximity reactivity
 * - Speech reactivity (modulates waveHeight, speed, hotspot, and center opacity on voice)
 */

class PlasmaRingController {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.options = Object.assign({
      colors: ['#FF1744', '#0055FF', '#FF0055', '#7928CA', '#00E5FF'],
      density: 100,
      speed: 70,
      waveHeight: 18,
      centerOpacity: 85,
      scale: 36,
      dragSensitivity: 100,
      tilt: 20,
      radius: 260,
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
    this.canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:auto;cursor:grab;';
    this.container.innerHTML = '';
    this.container.appendChild(this.canvas);

    const gl = this.canvas.getContext('webgl', {
      alpha: true,
      antialias: false,
      premultipliedAlpha: true,
      depth: false
    });

    if (!gl) {
      console.warn('WebGL not supported for PlasmaRing');
      return;
    }
    this.gl = gl;

    this.DPR_CAP = 1.5;
    this.FOV_DEG = 42;
    this.TAU = Math.PI * 2;
    this.MAX_COLORS = 5;

    this.initShaders();
    this.initBuffers();
    this.initEvents();
    this.startLoop();
  }

  initShaders() {
    const gl = this.gl;
    const MAX_COLORS = this.MAX_COLORS;

    const VERT = `
      precision highp float;
      attribute vec2 aPolar;
      attribute vec2 aRnd;

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
      uniform vec3  uColors[${MAX_COLORS}];
      uniform vec3  uHotspot;
      uniform vec3  uCamDir;

      uniform vec3  uHoverDir;
      uniform float uHoverRadius;
      uniform float uHoverPush;
      uniform float uHoverActive;

      varying vec3  vCol;
      varying float vAlpha;

      vec3 rampColor(float x) {
          float p  = clamp(x, 0.0, 1.0) * max(uColorCount - 1.0, 0.0);
          float i0 = floor(p);
          float f  = p - i0;
          vec3 a = uColors[0];
          vec3 b = uColors[0];
          for (int i = 0; i < ${MAX_COLORS}; i++) {
              if (float(i) == i0)       a = uColors[i];
              if (float(i) == i0 + 1.0) b = uColors[i];
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
              vAlpha = 0.0; vCol = vec3(0.0); return;
          }

          float sx  = x1 * uFocal / rz;
          float sy2 = y2 * uFocal / rz;
          gl_Position  = vec4(sx / (uRes.x * 0.5), sy2 / (uRes.y * 0.5), 0.0, 1.0);

          float rimDot  = abs(dot(norm, uCamDir));
          float fresnel = pow(max(1.0 - rimDot, 0.0), uRimPower);
          fresnel = max(fresnel, uCenter * rimDot);

          float hoverAlpha = hEffect * 0.95;
          float finalAlpha = max(fresnel, hoverAlpha);
          float bri = 0.50 + aRnd.x * 0.50;

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
          gl_FragColor = vec4(vCol * vAlpha, vAlpha);
      }
    `;

    const compile = (type, src) => {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
        console.error('PlasmaRing Shader Error:', gl.getShaderInfoLog(sh));
      }
      return sh;
    };

    const prog = gl.createProgram();
    const vs = compile(gl.VERTEX_SHADER, VERT);
    const fs = compile(gl.FRAGMENT_SHADER, FRAG);
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.error('PlasmaRing Program Link Error:', gl.getProgramInfoLog(prog));
    }
    this.prog = prog;

    const U = (name) => gl.getUniformLocation(prog, name);
    this.sA = {
      polar: gl.getAttribLocation(prog, 'aPolar'),
      rnd:   gl.getAttribLocation(prog, 'aRnd')
    };

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
      colors: U('uColors[0]'),
      hotspot: U('uHotspot'), camDir: U('uCamDir'),
      hoverDir: U('uHoverDir'), hoverRadius: U('uHoverRadius'),
      hoverPush: U('uHoverPush'), hoverActive: U('uHoverActive')
    };
  }

  initBuffers() {
    const gl = this.gl;
    const d = this.options.density;
    const TAU = this.TAU;

    const N_theta = Math.max(60, Math.round(d * 2.5));
    const N_phi   = Math.max(40, Math.round(d * 1.8));
    this.count = N_theta * N_phi;

    const polarA = new Float32Array(this.count * 2);
    const rndA   = new Float32Array(this.count * 2);

    let seed = 0xc0ffee7;
    const rnd = () => {
      seed |= 0;
      seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed) ^ seed;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };

    let i = 0;
    for (let ti = 0; ti < N_theta; ti++) {
      const theta = (ti + 0.5) / N_theta * TAU;
      for (let pi = 0; pi < N_phi; pi++) {
        const phi = ((pi + 0.5) / N_phi - 0.5) * Math.PI;
        polarA[i * 2]     = phi;
        polarA[i * 2 + 1] = theta;
        rndA[i * 2]       = rnd();
        rndA[i * 2 + 1]   = rnd();
        i++;
      }
    }

    const numMeridianSegments = N_theta * (N_phi - 1);
    const numParallelSegments = N_phi * N_theta;
    this.indexCount = (numMeridianSegments + numParallelSegments) * 2;
    const indices = new Uint16Array(this.indexCount);
    let idx = 0;

    for (let ti = 0; ti < N_theta; ti++) {
      for (let pi = 0; pi < N_phi - 1; pi++) {
        const curr = ti * N_phi + pi;
        const next = ti * N_phi + (pi + 1);
        indices[idx++] = curr;
        indices[idx++] = next;
      }
    }

    for (let pi = 0; pi < N_phi; pi++) {
      for (let ti = 0; ti < N_theta; ti++) {
        const curr = ti * N_phi + pi;
        const next = ((ti + 1) % N_theta) * N_phi + pi;
        indices[idx++] = curr;
        indices[idx++] = next;
      }
    }

    this.polarBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.polarBuf);
    gl.bufferData(gl.ARRAY_BUFFER, polarA, gl.STATIC_DRAW);

    this.rndBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.rndBuf);
    gl.bufferData(gl.ARRAY_BUFFER, rndA, gl.STATIC_DRAW);

    this.idxBuf = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.idxBuf);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);

    gl.disable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
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
    this.hov = { active: 0, target: 0, miss: 1, dirX: 0, dirY: 1, dirZ: 0, mx: 0, my: 0 };

    const onDown = (e) => {
      this.drag.active = true;
      this.drag.lastX = e.clientX;
      this.drag.lastY = e.clientY;
      this.canvas.style.cursor = 'grabbing';
    };

    const onMove = (e) => {
      const r = this.canvas.getBoundingClientRect();
      this.hov.mx = e.clientX - r.left;
      this.hov.my = e.clientY - r.top;
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

    const onLeave = () => {
      this.hov.target = 0;
    };

    this.canvas.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    this.canvas.addEventListener('mouseleave', onLeave);

    // Touch support
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

    const palBuf = new Float32Array(this.MAX_COLORS * 3);
    const colors = this.options.colors;
    for (let i = 0; i < this.MAX_COLORS; i++) {
      const c = colors[Math.min(i, colors.length - 1)];
      const [r, g, b] = this.parseColor(c);
      palBuf[i * 3]     = r;
      palBuf[i * 3 + 1] = g;
      palBuf[i * 3 + 2] = b;
    }

    const CAM_FAR = 2100;
    const CAM_PER_SCALE = 15;

    const frame = (now) => {
      this.raf = requestAnimationFrame(frame);
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;
      elapsed += dt;

      // Handle canvas resize
      const dpr = Math.min(window.devicePixelRatio || 1, this.DPR_CAP);
      const w = Math.round((this.canvas.clientWidth || 300) * dpr);
      const h = Math.round((this.canvas.clientHeight || 300) * dpr);
      if (this.canvas.width !== w || this.canvas.height !== h) {
        this.canvas.width = w;
        this.canvas.height = h;
        gl.viewport(0, 0, w, h);
      }

      // Smooth voice reactivity transition
      this.voiceCurrent += (this.voiceTarget - this.voiceCurrent) * 0.12;

      // Camera damping
      const damp = 1 - Math.pow(this.options.orbitDamping / 100, dt * 10);
      this.cam.yaw   += this.cam.yawV * damp;
      this.cam.pitch += this.cam.pitchV * damp;
      this.cam.yaw   = ((this.cam.yaw   + Math.PI) % this.TAU + this.TAU) % this.TAU - Math.PI;
      this.cam.pitch = ((this.cam.pitch + Math.PI) % this.TAU + this.TAU) % this.TAU - Math.PI;
      this.cam.yawV   *= (1 - damp * 1.4);
      this.cam.pitchV *= (1 - damp * 1.4);

      // Auto subtle idle rotation if not dragged
      if (!this.drag.active) {
        this.cam.yaw += (0.15 + this.voiceCurrent * 0.45) * dt;
      }

      // Hover interpolation
      this.hov.active += (this.hov.target - this.hov.active) * 0.1;

      const focal = h / (2 * Math.tan((this.FOV_DEG / 2) * Math.PI / 180));
      const totalPitch = this.cam.pitch + (this.options.tilt * Math.PI) / 180;

      const cy  = Math.cos(this.cam.yaw), sy = Math.sin(this.cam.yaw);
      const ctp = Math.cos(totalPitch),   stp = Math.sin(totalPitch);
      const cdx = -sy * ctp;
      const cdy =  stp;
      const cdz =  cy * ctp;
      const cdl = Math.sqrt(cdx * cdx + cdy * cdy + cdz * cdz) || 1;

      // Dynamic reactive parameters: voice amplifies waves, speed, and brightness
      const voiceAmp = this.voiceCurrent;
      const dynamicWaveHeight = this.options.waveHeight * (1.0 + voiceAmp * 1.8);
      const dynamicWaveSpeed = this.options.speed * (1.0 + voiceAmp * 1.5);
      const dynamicCenter = (this.options.centerOpacity / 100) * (1.0 + voiceAmp * 0.6);

      const [tr, tg, tb] = this.parseColor(colors[0]);
      const hr = Math.min(1, tr * (0.6 + voiceAmp * 0.4) + 0.8);
      const hg = Math.min(1, tg * 0.4 + 0.7);
      const hb = Math.min(1, tb * 0.5 + 0.8);

      const cameraDistance = CAM_FAR - CAM_PER_SCALE * this.options.scale;
      const timeVal = elapsed * (dynamicWaveSpeed / 50);

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
      gl.uniform3fv(this.sU.colors, palBuf);
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
      gl.vertexAttribPointer(this.sA.rnd, 2, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.idxBuf);
      gl.drawElements(gl.LINES, this.indexCount, gl.UNSIGNED_SHORT, 0);
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
