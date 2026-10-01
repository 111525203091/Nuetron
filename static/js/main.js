/**
 * MONSTER JUICE - 3D WEBGL & FLASHING ENGINE
 * High-voltage 3D graphics, electric lightning, and audio synthesis.
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Global State ---
    let soundEnabled = true;
    let overdriveActive = true;
    let audioCtx = null;
    let currentFlavor = 'mango-loco';

    const flavorConfigs = {
        'mango-loco': {
            name: 'MANGO LOCO',
            primary: '#ff5900',
            secondary: '#00d2ff',
            glow: 'rgba(255, 89, 0, 0.55)',
            glowIntense: 'rgba(255, 89, 0, 0.9)',
            hexInt: 0xff5900,
            secHexInt: 0x00d2ff,
            clawColors: ['#00d2ff', '#52ff00', '#ff5900'],
            tagline: 'A Heavenly Blend of Exotic Juices',
            badge: '⚡ OVERDRIVE FLAVOR DROP',
            juice: '16% Real Fruit Puree',
            calories: '210',
            bgGrad: ['#120800', '#3b1600', '#ff5900', '#ff8533']
        },
        'pipeline-punch': {
            name: 'PIPELINE PUNCH',
            primary: '#ff007b',
            secondary: '#ff9e00',
            glow: 'rgba(255, 0, 123, 0.55)',
            glowIntense: 'rgba(255, 0, 123, 0.9)',
            hexInt: 0xff007b,
            secHexInt: 0xff9e00,
            clawColors: ['#ff007b', '#ff9e00', '#ff4d94'],
            tagline: 'The Banzai Beast of the North Shore',
            badge: '⚡ COASTAL WAVE DROP',
            juice: '16% Real Hawaiian Blend',
            calories: '200',
            bgGrad: ['#16000c', '#3d0021', '#ff007b', '#ff4d94']
        },
        'khaotic': {
            name: 'KHAOTIC',
            primary: '#ffaa00',
            secondary: '#52ff00',
            glow: 'rgba(255, 170, 0, 0.55)',
            glowIntense: 'rgba(255, 170, 0, 0.9)',
            hexInt: 0xffaa00,
            secHexInt: 0x52ff00,
            clawColors: ['#52ff00', '#ffaa00', '#ff4400'],
            tagline: 'Pure Citrus Carnage Re-Engineered',
            badge: '⚡ RE-ENGINEERED CLASSIC',
            juice: '10% Real Citrus Juice',
            calories: '190',
            bgGrad: ['#140e00', '#3a2400', '#ffaa00', '#ffc44d']
        },
        'pacific-punch': {
            name: 'PACIFIC PUNCH',
            primary: '#e60026',
            secondary: '#ffd700',
            glow: 'rgba(230, 0, 38, 0.55)',
            glowIntense: 'rgba(230, 0, 38, 0.9)',
            hexInt: 0xe60026,
            secHexInt: 0xffd700,
            clawColors: ['#ffd700', '#e60026', '#880015'],
            tagline: 'Old School Punch with Tattoo Soul',
            badge: '⚡ TRADITIONAL HIGH TIDE',
            juice: '12% Tropical Red Punch',
            calories: '210',
            bgGrad: ['#150005', '#38000f', '#e60026', '#ff3355']
        },
        'aussie-lemonade': {
            name: 'AUSSIE LEMONADE',
            primary: '#00e5ff',
            secondary: '#ccff00',
            glow: 'rgba(0, 229, 255, 0.55)',
            glowIntense: 'rgba(0, 229, 255, 0.9)',
            hexInt: 0x00e5ff,
            secHexInt: 0xccff00,
            clawColors: ['#00e5ff', '#ccff00', '#00b4d8'],
            tagline: 'Land Down Under Exotic Citrus Storm',
            badge: '⚡ SUB-TROPICAL RUSH',
            juice: '11% Meyer Lemon & Citrus',
            calories: '180',
            bgGrad: ['#001317', '#00313a', '#00e5ff', '#66efff']
        }
    };

    // ==========================================================
    // 1. SCREEN STROBE FLASH & SHAKE SYSTEM
    // ==========================================================
    const strobeFlashEl = document.getElementById('strobeFlash');

    function triggerScreenStrobe(type = 'white') {
        if (!overdriveActive || !strobeFlashEl) return;

        // Apply flash class
        strobeFlashEl.className = 'strobe-flash';
        void strobeFlashEl.offsetWidth; // Force reflow
        strobeFlashEl.classList.add(type === 'color' ? 'flash-color' : 'flash-white');

        // Trigger camera shake on body
        document.body.classList.remove('screen-shake');
        void document.body.offsetWidth;
        document.body.classList.add('screen-shake');

        setTimeout(() => {
            if (strobeFlashEl) strobeFlashEl.className = 'strobe-flash';
        }, 80);

        setTimeout(() => {
            document.body.classList.remove('screen-shake');
        }, 360);
    }

    // Overdrive Toggle Button
    const overdriveBtn = document.getElementById('overdriveToggleBtn');
    if (overdriveBtn) {
        overdriveBtn.addEventListener('click', () => {
            overdriveActive = !overdriveActive;
            document.body.classList.toggle('overdrive-active', overdriveActive);
            overdriveBtn.classList.toggle('active', overdriveActive);
            overdriveBtn.querySelector('.btn-text').textContent = overdriveActive ? '⚡ STROBE FX: ON' : '⚡ STROBE FX: OFF';
            if (overdriveActive) {
                triggerScreenStrobe('white');
                playElectricShockSound();
            }
        });
    }

    // ==========================================================
    // 2. PROCEDURAL LIGHTNING STORM CANVAS
    // ==========================================================
    const lightningCanvas = document.getElementById('lightningCanvas');
    let lightningCtx = null;
    let lightningTimer = null;

    if (lightningCanvas) {
        lightningCtx = lightningCanvas.getContext('2d');
        const resizeLightning = () => {
            lightningCanvas.width = window.innerWidth;
            lightningCanvas.height = window.innerHeight;
        };
        resizeLightning();
        window.addEventListener('resize', resizeLightning);
    }

    function createLightningBranch(startX, startY, endX, endY, depth = 0) {
        if (!lightningCtx || depth > 4) return;

        const config = flavorConfigs[currentFlavor] || flavorConfigs['mango-loco'];
        const dx = endX - startX;
        const dy = endY - startY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 15) {
            lightningCtx.beginPath();
            lightningCtx.moveTo(startX, startY);
            lightningCtx.lineTo(endX, endY);
            lightningCtx.strokeStyle = depth === 0 ? '#ffffff' : config.secondary;
            lightningCtx.lineWidth = Math.max(1, 4 - depth);
            lightningCtx.shadowColor = config.primary;
            lightningCtx.shadowBlur = 20;
            lightningCtx.stroke();
            return;
        }

        // Jagged offset
        const midX = (startX + endX) / 2 + (Math.random() - 0.5) * distance * 0.45;
        const midY = (startY + endY) / 2 + (Math.random() - 0.5) * distance * 0.25;

        createLightningBranch(startX, startY, midX, midY, depth);
        createLightningBranch(midX, midY, endX, endY, depth);

        // Occasional branch shoot
        if (Math.random() < 0.35 && depth < 3) {
            const branchEndX = midX + (Math.random() - 0.5) * 160;
            const branchEndY = midY + Math.random() * 120 + 30;
            createLightningBranch(midX, midY, branchEndX, branchEndY, depth + 1);
        }
    }

    function triggerLightningStrike(x = null, y = null) {
        if (!lightningCtx || !overdriveActive) return;

        lightningCtx.clearRect(0, 0, lightningCanvas.width, lightningCanvas.height);
        const startX = x !== null ? x : Math.random() * lightningCanvas.width;
        const startY = 0;
        const endX = startX + (Math.random() - 0.5) * 300;
        const endY = y !== null ? y : lightningCanvas.height * (0.6 + Math.random() * 0.4);

        createLightningBranch(startX, startY, endX, endY, 0);

        // Flash fadeout
        let alpha = 1.0;
        const fade = () => {
            alpha -= 0.15;
            if (alpha > 0) {
                lightningCtx.fillStyle = `rgba(7, 8, 10, 0.25)`;
                lightningCtx.fillRect(0, 0, lightningCanvas.width, lightningCanvas.height);
                requestAnimationFrame(fade);
            } else {
                lightningCtx.clearRect(0, 0, lightningCanvas.width, lightningCanvas.height);
            }
        };
        setTimeout(fade, 60);
    }

    // Ambient lightning loop
    function scheduleNextLightning() {
        const delay = overdriveActive ? (Math.random() * 4000 + 2000) : (Math.random() * 9000 + 5000);
        lightningTimer = setTimeout(() => {
            if (overdriveActive && Math.random() > 0.4) {
                triggerLightningStrike();
                if (Math.random() > 0.6) triggerScreenStrobe('color');
            }
            scheduleNextLightning();
        }, delay);
    }
    scheduleNextLightning();

    // ==========================================================
    // 3. SYNTHESIZED WEB AUDIO API (CAN POP, FIZZ & LIGHTNING ZAP)
    // ==========================================================
    function initAudio() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    function playCanCrackSound() {
        if (!soundEnabled) return;
        try {
            initAudio();
            const now = audioCtx.currentTime;

            // 1. Violent Metallic Snap & Pop
            const osc = audioCtx.createOscillator();
            const oscGain = audioCtx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(600, now);
            osc.frequency.exponentialRampToValueAtTime(65, now + 0.09);

            oscGain.gain.setValueAtTime(0.9, now);
            oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);

            osc.connect(oscGain);
            oscGain.connect(audioCtx.destination);
            osc.start(now);
            osc.stop(now + 0.12);

            // 2. High-Pressure White Noise Fizz Hiss
            const bufferSize = audioCtx.sampleRate * 0.55;
            const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
            const data = buffer.getChannelData(0);
            for (let i = 0; i < bufferSize; i++) {
                data[i] = (Math.random() * 2 - 1);
            }

            const noiseNode = audioCtx.createBufferSource();
            noiseNode.buffer = buffer;

            const filter = audioCtx.createBiquadFilter();
            filter.type = 'bandpass';
            filter.frequency.setValueAtTime(3600, now);
            filter.Q.setValueAtTime(2.5, now);

            const noiseGain = audioCtx.createGain();
            noiseGain.gain.setValueAtTime(0.65, now);
            noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.55);

            noiseNode.connect(filter);
            filter.connect(noiseGain);
            noiseGain.connect(audioCtx.destination);
            noiseNode.start(now + 0.03);
            noiseNode.stop(now + 0.6);

            // 3. Sub-bass boom
            const sub = audioCtx.createOscillator();
            const subGain = audioCtx.createGain();
            sub.type = 'sine';
            sub.frequency.setValueAtTime(120, now);
            sub.frequency.exponentialRampToValueAtTime(35, now + 0.25);
            subGain.gain.setValueAtTime(0.6, now);
            subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

            sub.connect(subGain);
            subGain.connect(audioCtx.destination);
            sub.start(now);
            sub.stop(now + 0.32);

        } catch (e) {
            console.warn("Audio Context error:", e);
        }
    }

    function playElectricShockSound() {
        if (!soundEnabled) return;
        try {
            initAudio();
            const now = audioCtx.currentTime;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(180, now);
            osc.frequency.setValueAtTime(850, now + 0.05);
            osc.frequency.exponentialRampToValueAtTime(90, now + 0.18);

            gain.gain.setValueAtTime(0.4, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now);
            osc.stop(now + 0.22);
        } catch (e) {}
    }

    const soundBtn = document.getElementById('soundToggleBtn');
    if (soundBtn) {
        soundBtn.addEventListener('click', () => {
            soundEnabled = !soundEnabled;
            soundBtn.innerHTML = soundEnabled ? '<span>🔊 AUDIO ON</span>' : '<span>🔇 AUDIO OFF</span>';
        });
    }

    // ==========================================================
    // 4. THREE.JS REAL 3D CYLINDER CAN ENGINE
    // ==========================================================
    const canvas3D = document.getElementById('threeCanCanvas');
    let renderer, scene, camera, canGroup, canBodyMesh, canTexture, canTextureCanvas, canTextureCtx;
    let flavorPointLight, rimPointLight;
    let floatingCrystals = [];

    // Mouse drag rotation state
    let isDragging = false;
    let prevMousePos = { x: 0, y: 0 };
    let rotSpeed = { x: 0, y: 0.008 };
    let turboSpinSpeed = 0;

    function createProceduralCanTexture(flavorId) {
        const config = flavorConfigs[flavorId] || flavorConfigs['mango-loco'];

        if (!canTextureCanvas) {
            canTextureCanvas = document.createElement('canvas');
            canTextureCanvas.width = 1024;
            canTextureCanvas.height = 1024;
            canTextureCtx = canTextureCanvas.getContext('2d');
        }

        const ctx = canTextureCtx;
        const w = 1024;
        const h = 1024;

        // 1. Can body dark metallic gradient background
        const grad = ctx.createLinearGradient(0, 0, w, 0);
        grad.addColorStop(0, '#111419');
        grad.addColorStop(0.2, '#1b2029');
        grad.addColorStop(0.48, config.primary);
        grad.addColorStop(0.55, '#ffffff');
        grad.addColorStop(0.65, config.primary);
        grad.addColorStop(0.85, '#1e2430');
        grad.addColorStop(1, '#0c0e12');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // 2. High-speed grunge cyber stripes
        ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
        for (let i = 0; i < 8; i++) {
            ctx.beginPath();
            ctx.moveTo(0, i * 140);
            ctx.lineTo(w, i * 140 + 200);
            ctx.lineTo(w, i * 140 + 230);
            ctx.lineTo(0, i * 140 + 30);
            ctx.fill();
        }

        // 3. Top Banner
        ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
        ctx.fillRect(100, 100, w - 200, 75);
        ctx.fillStyle = '#ffffff';
        ctx.font = '900 38px "Orbitron", sans-serif';
        ctx.textAlign = 'center';
        ctx.letterSpacing = '6px';
        ctx.fillText('JUICE MONSTER', w / 2, 150);

        // 4. ICONIC MONSTER 3-CLAW RIP MARK
        ctx.save();
        ctx.translate(w / 2, 450);
        ctx.shadowColor = config.primary;
        ctx.shadowBlur = 35;

        // Draw Left Claw
        ctx.fillStyle = config.clawColors[0];
        ctx.beginPath();
        ctx.moveTo(-110, -160);
        ctx.quadraticCurveTo(-70, 0, -115, 170);
        ctx.quadraticCurveTo(-140, 110, -135, -20);
        ctx.closePath();
        ctx.fill();

        // Draw Middle Claw
        ctx.fillStyle = config.clawColors[1];
        ctx.beginPath();
        ctx.moveTo(0, -210);
        ctx.quadraticCurveTo(25, 0, -10, 220);
        ctx.quadraticCurveTo(-30, 80, -25, -120);
        ctx.closePath();
        ctx.fill();

        // Draw Right Claw
        ctx.fillStyle = config.clawColors[2];
        ctx.beginPath();
        ctx.moveTo(110, -160);
        ctx.quadraticCurveTo(140, 20, 95, 170);
        ctx.quadraticCurveTo(80, 70, 85, -40);
        ctx.closePath();
        ctx.fill();

        ctx.restore();

        // 5. Flavor Title
        ctx.fillStyle = '#ffffff';
        ctx.font = '900 68px "Orbitron", sans-serif';
        ctx.textAlign = 'center';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 15;
        ctx.fillText(config.name, w / 2, 770);

        // Subtext
        ctx.fillStyle = config.secondary;
        ctx.font = '700 28px "Inter", sans-serif';
        ctx.fillText('+ ENERGY BLEND + REAL JUICE', w / 2, 820);

        // Volume text
        ctx.fillStyle = '#94a3b8';
        ctx.font = '600 22px "Inter", sans-serif';
        ctx.fillText('16 FL. OZ. (473 mL)', w / 2, 940);

        return canTextureCanvas;
    }

    function initThreeJS() {
        if (!canvas3D || typeof THREE === 'undefined') return;

        const stage = document.getElementById('webglCanStage');
        const width = stage.clientWidth || 360;
        const height = stage.clientHeight || 560;

        // Scene
        scene = new THREE.Scene();

        // Camera
        camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
        camera.position.set(0, 0, 8.8);

        // Renderer
        renderer = new THREE.WebGLRenderer({
            canvas: canvas3D,
            alpha: true,
            antialias: true
        });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.1;

        // Group container
        canGroup = new THREE.Group();
        scene.add(canGroup);

        // Procedural Label Texture
        const canvasTex = createProceduralCanTexture('mango-loco');
        canTexture = new THREE.CanvasTexture(canvasTex);
        canTexture.anisotropy = 8;

        // --- Materials ---
        const canBodyMaterial = new THREE.MeshStandardMaterial({
            map: canTexture,
            roughness: 0.28,
            metalness: 0.65
        });

        const silverMetalMaterial = new THREE.MeshStandardMaterial({
            color: 0xd9e1e8,
            metalness: 0.95,
            roughness: 0.18
        });

        const darkMetalMaterial = new THREE.MeshStandardMaterial({
            color: 0x475569,
            metalness: 0.8,
            roughness: 0.35
        });

        // 1. Can Body Cylinder
        const bodyGeo = new THREE.CylinderGeometry(1.4, 1.4, 4.3, 48, 1, true);
        canBodyMesh = new THREE.Mesh(bodyGeo, canBodyMaterial);
        canGroup.add(canBodyMesh);

        // 2. Can Top Taper Neck
        const neckGeo = new THREE.CylinderGeometry(1.22, 1.4, 0.38, 48);
        const neckMesh = new THREE.Mesh(neckGeo, silverMetalMaterial);
        neckMesh.position.y = 2.34;
        canGroup.add(neckMesh);

        // 3. Top Rim Ring
        const rimGeo = new THREE.TorusGeometry(1.22, 0.05, 16, 48);
        const rimMesh = new THREE.Mesh(rimGeo, silverMetalMaterial);
        rimMesh.rotation.x = Math.PI / 2;
        rimMesh.position.y = 2.53;
        canGroup.add(rimMesh);

        // 4. Top Lid Cover
        const lidGeo = new THREE.CylinderGeometry(1.2, 1.2, 0.04, 36);
        const lidMesh = new THREE.Mesh(lidGeo, darkMetalMaterial);
        lidMesh.position.y = 2.51;
        canGroup.add(lidMesh);

        // 5. Pull Tab Opener
        const tabGeo = new THREE.BoxGeometry(0.35, 0.04, 0.65);
        const tabMesh = new THREE.Mesh(tabGeo, silverMetalMaterial);
        tabMesh.position.set(0, 2.55, 0.25);
        canGroup.add(tabMesh);

        // 6. Bottom Bevel Taper
        const bottomGeo = new THREE.CylinderGeometry(1.4, 1.15, 0.35, 48);
        const bottomMesh = new THREE.Mesh(bottomGeo, silverMetalMaterial);
        bottomMesh.position.y = -2.32;
        canGroup.add(bottomMesh);

        // 7. Floating 3D Juice Particles / Carbonation Orbs in Chamber
        const orbGeo = new THREE.SphereGeometry(0.08, 12, 12);
        for (let i = 0; i < 40; i++) {
            const orbMat = new THREE.MeshBasicMaterial({
                color: flavorConfigs['mango-loco'].hexInt,
                transparent: true,
                opacity: Math.random() * 0.6 + 0.3
            });
            const orb = new THREE.Mesh(orbGeo, orbMat);
            orb.position.set(
                (Math.random() - 0.5) * 5.5,
                (Math.random() - 0.5) * 6.5,
                (Math.random() - 0.5) * 4.5
            );
            orb.userData = {
                speedY: Math.random() * 0.015 + 0.005,
                angle: Math.random() * Math.PI * 2,
                radius: Math.random() * 2.5 + 1.8
            };
            canGroup.add(orb);
            floatingCrystals.push(orb);
        }

        // --- Lights ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 1.6);
        dirLight.position.set(3, 4, 6);
        scene.add(dirLight);

        flavorPointLight = new THREE.PointLight(flavorConfigs['mango-loco'].hexInt, 3.5, 9);
        flavorPointLight.position.set(-2.5, 1, 3.5);
        scene.add(flavorPointLight);

        rimPointLight = new THREE.PointLight(flavorConfigs['mango-loco'].secHexInt, 2.8, 8);
        rimPointLight.position.set(2.8, -1.5, -2.5);
        scene.add(rimPointLight);

        // Tilt initial can slightly for natural 3D posture
        canGroup.rotation.x = 0.12;
        canGroup.rotation.z = -0.06;

        // --- Drag Controls ---
        const dom = stage;
        dom.addEventListener('mousedown', (e) => {
            isDragging = true;
            prevMousePos = { x: e.clientX, y: e.clientY };
            rotSpeed.y = 0;
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
        });

        window.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const deltaX = e.clientX - prevMousePos.x;
                const deltaY = e.clientY - prevMousePos.y;
                canGroup.rotation.y += deltaX * 0.012;
                canGroup.rotation.x += deltaY * 0.008;
                prevMousePos = { x: e.clientX, y: e.clientY };
            }
        });

        // Touch support
        dom.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                isDragging = true;
                prevMousePos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
        });

        window.addEventListener('touchend', () => {
            isDragging = false;
        });

        window.addEventListener('touchmove', (e) => {
            if (isDragging && e.touches.length === 1) {
                const deltaX = e.touches[0].clientX - prevMousePos.x;
                const deltaY = e.touches[0].clientY - prevMousePos.y;
                canGroup.rotation.y += deltaX * 0.015;
                canGroup.rotation.x += deltaY * 0.01;
                prevMousePos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
        });

        // Resize handler
        window.addEventListener('resize', () => {
            const w = stage.clientWidth || 360;
            const h = stage.clientHeight || 560;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });

        // Render Loop
        function animate() {
            requestAnimationFrame(animate);

            if (!isDragging) {
                // Auto idle rotation
                const currentIdleSpeed = 0.008 + turboSpinSpeed;
                canGroup.rotation.y += currentIdleSpeed;

                // Decay turbo spin smoothly
                if (turboSpinSpeed > 0) {
                    turboSpinSpeed *= 0.94;
                    if (turboSpinSpeed < 0.001) turboSpinSpeed = 0;
                }
            }

            // Animate floating juice spheres
            floatingCrystals.forEach(orb => {
                orb.position.y += orb.userData.speedY;
                if (orb.position.y > 3.2) {
                    orb.position.y = -3.2;
                }
            });

            renderer.render(scene, camera);
        }
        animate();
    }

    initThreeJS();

    // Turbo spin 360 button
    const spinBtn = document.getElementById('spinCanBtn');
    if (spinBtn) {
        spinBtn.addEventListener('click', () => {
            turboSpinSpeed = 0.28;
            playCanCrackSound();
            triggerScreenStrobe('color');
        });
    }

    // Update 3D Can Texture & Lights when flavor changes
    function update3DCanFlavor(flavorId) {
        const config = flavorConfigs[flavorId] || flavorConfigs['mango-loco'];
        createProceduralCanTexture(flavorId);
        if (canTexture) {
            canTexture.needsUpdate = true;
        }

        if (flavorPointLight) {
            flavorPointLight.color.setHex(config.hexInt);
        }
        if (rimPointLight) {
            rimPointLight.color.setHex(config.secHexInt);
        }

        floatingCrystals.forEach(orb => {
            orb.material.color.setHex(config.hexInt);
        });

        // Ambient glow light background update
        const glowDisc = document.getElementById('canAmbientLight');
        if (glowDisc) {
            glowDisc.style.background = `radial-gradient(circle, ${config.glowIntense} 0%, transparent 70%)`;
        }
    }

    // ==========================================================
    // 5. FLAVOR SWITCHING ENGINE & SYNCHRONIZATION
    // ==========================================================
    function setFlavor(flavorId) {
        currentFlavor = flavorId;
        const config = flavorConfigs[flavorId] || flavorConfigs['mango-loco'];

        // CSS Variables update
        document.documentElement.style.setProperty('--accent-color', config.primary);
        document.documentElement.style.setProperty('--accent-secondary', config.secondary);
        document.documentElement.style.setProperty('--accent-glow', config.glow);
        document.documentElement.style.setProperty('--accent-glow-intense', config.glowIntense);

        document.body.setAttribute('data-active-flavor', flavorId);

        // Update pills
        document.querySelectorAll('.flavor-pill').forEach(p => {
            p.classList.toggle('active', p.dataset.flavorId === flavorId);
        });

        // Update Hero Text Elements
        const titleEl = document.getElementById('heroFlavorTitle');
        const taglineEl = document.getElementById('heroTagline');
        const badgeEl = document.getElementById('heroBadge');
        const juiceEl = document.getElementById('metricJuice');
        const calEl = document.getElementById('metricCalories');

        if (titleEl) titleEl.textContent = config.name;
        if (taglineEl) taglineEl.textContent = config.tagline;
        if (badgeEl) badgeEl.textContent = config.badge;
        if (juiceEl) juiceEl.textContent = config.juice.split(' ')[0];
        if (calEl) calEl.textContent = config.calories;

        // Update 3D Can in Three.js
        update3DCanFlavor(flavorId);

        // Trigger Flashing & SFX
        triggerScreenStrobe('white');
        triggerLightningStrike();
        playCanCrackSound();
    }

    // Flavor Pill click listeners
    document.querySelectorAll('.flavor-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            setFlavor(pill.dataset.flavorId);
        });
    });

    // 3D Flavor card buttons
    document.querySelectorAll('.select-flavor-btn-3d').forEach(btn => {
        btn.addEventListener('click', () => {
            const fid = btn.dataset.flavorId;
            setFlavor(fid);
            document.getElementById('hero').scrollIntoView({ behavior: 'smooth' });
        });
    });

    // Footer quick links
    document.querySelectorAll('.quick-flavor').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const fid = link.dataset.fid;
            setFlavor(fid);
            document.getElementById('hero').scrollIntoView({ behavior: 'smooth' });
        });
    });

    // ==========================================================
    // 6. CRACK THE CAN HERO TRIGGER
    // ==========================================================
    const crackHeroBtn = document.getElementById('crackCanHeroBtn');
    if (crackHeroBtn) {
        crackHeroBtn.addEventListener('click', () => {
            turboSpinSpeed = 0.22;
            triggerScreenStrobe('white');
            triggerLightningStrike(window.innerWidth / 2, window.innerHeight * 0.4);
            playCanCrackSound();
        });
    }

    // ==========================================================
    // 7. INTERACTIVE 3D MOUSE PARALLAX ON CARDS
    // ==========================================================
    document.querySelectorAll('.card-3d-tilt').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            const rotateX = (-y / rect.height) * 14;
            const rotateY = (x / rect.width) * 14;
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)`;
        });
    });

    // ==========================================================
    // 8. INTERACTIVE VIBE SYNTHESIZER LAB
    // ==========================================================
    const sliderSweetness = document.getElementById('sliderSweetness');
    const sliderIntensity = document.getElementById('sliderIntensity');
    const sliderAesthetic = document.getElementById('sliderAesthetic');

    const valSweet = document.getElementById('valSweet');
    const valIntensity = document.getElementById('valIntensity');
    const valAesthetic = document.getElementById('valAesthetic');

    const resultName = document.getElementById('resultName');
    const resultReason = document.getElementById('resultReason');
    const lockMatchBtn = document.getElementById('lockMatchBtn');

    let matchedFlavorId = 'pipeline-punch';

    function evaluateVibe() {
        const s = parseInt(sliderSweetness.value);
        const intensity = parseInt(sliderIntensity.value);
        const aes = parseInt(sliderAesthetic.value);

        const sweetLabels = ["Sub-Zero Tart", "Crisp Tangy", "Balanced Punch", "Tropical Sweet", "Rich Puree Nectar"];
        const intensityLabels = ["All-Day Cruise", "Pre-Session Focus", "Apex Savage Drive"];
        const aesLabels = ["Día de Muertos", "North Shore Oahu", "Urban Street Rebel", "Aussie Wilderness"];

        if (valSweet) valSweet.textContent = sweetLabels[s - 1] || "";
        if (valIntensity) valIntensity.textContent = intensityLabels[intensity - 1] || "";
        if (valAesthetic) valAesthetic.textContent = aesLabels[aes - 1] || "";

        if (aes === 1 || s >= 5) {
            matchedFlavorId = 'mango-loco';
            resultName.textContent = 'MANGO LOCO';
            resultReason.textContent = 'Rich exotic mango and guava puree with supernatural tropical sweetness.';
        } else if (aes === 2 || s === 4) {
            matchedFlavorId = 'pipeline-punch';
            resultName.textContent = 'PIPELINE PUNCH';
            resultReason.textContent = 'Hawaiian passionfruit, orange, and velvet guava with smooth coastal energy.';
        } else if (aes === 4 || s === 1) {
            matchedFlavorId = 'aussie-lemonade';
            resultName.textContent = 'AUSSIE LEMONADE';
            resultReason.textContent = 'Electric tart citrus and crisp lemon fizz inspired by Australia’s coastal outback.';
        } else if (s === 2) {
            matchedFlavorId = 'khaotic';
            resultName.textContent = 'KHAOTIC';
            resultReason.textContent = 'Re-engineered citrus punch with maximum tang and relentless adrenaline.';
        } else {
            matchedFlavorId = 'pacific-punch';
            resultName.textContent = 'PACIFIC PUNCH';
            resultReason.textContent = 'Traditional cherry-apple fruit punch backed by tattoo soul and pure torque.';
        }
    }

    if (sliderSweetness && sliderIntensity && sliderAesthetic) {
        [sliderSweetness, sliderIntensity, sliderAesthetic].forEach(sl => {
            sl.addEventListener('input', () => {
                evaluateVibe();
                if (overdriveActive && Math.random() > 0.7) triggerLightningStrike();
            });
        });
        evaluateVibe();
    }

    if (lockMatchBtn) {
        lockMatchBtn.addEventListener('click', () => {
            setFlavor(matchedFlavorId);
            document.getElementById('hero').scrollIntoView({ behavior: 'smooth' });
        });
    }

    // ==========================================================
    // 9. STORE FINDER AJAX
    // ==========================================================
    const storeForm = document.getElementById('storeFinderForm');
    const storeResults = document.getElementById('storeResults');

    if (storeForm) {
        storeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const zipInput = document.getElementById('zipInput');
            const zip = zipInput.value.trim();
            if (!zip) return;

            triggerScreenStrobe('color');
            playElectricShockSound();
            storeResults.innerHTML = '<div style="color: var(--text-muted); text-align:center; padding:1.5rem;">Radar scanning local cold vaults...</div>';

            try {
                const res = await fetch('/api/find-stores', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ zip_code: zip })
                });
                const data = await res.json();

                if (data.success && data.stores.length > 0) {
                    storeResults.innerHTML = data.stores.map(s => `
                        <div class="store-item">
                            <div>
                                <div class="store-name">${s.name}</div>
                                <div class="store-addr">${s.address}</div>
                            </div>
                            <div class="store-status">
                                <div class="store-stock">${s.stock}</div>
                                <div class="store-dist">${s.distance} away</div>
                            </div>
                        </div>
                    `).join('');
                } else {
                    storeResults.innerHTML = '<div style="color: #ff4444; padding:1rem;">No retailer found for this area. Check neighboring zip codes!</div>';
                }
            } catch (err) {
                storeResults.innerHTML = '<div style="color: #ff4444; padding:1rem;">Error searching cold vaults. Please try again.</div>';
            }
        });
    }

    // ==========================================================
    // 10. PROMO VOUCHER AJAX
    // ==========================================================
    const promoForm = document.getElementById('promoForm');
    const promoFeedback = document.getElementById('promoFeedback');

    if (promoForm) {
        promoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('promoEmail');
            const email = emailInput.value.trim();
            if (!email) return;

            triggerScreenStrobe('white');
            playCanCrackSound();

            try {
                const res = await fetch('/api/claim-promo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, flavor: currentFlavor })
                });
                const data = await res.json();

                if (data.success) {
                    promoFeedback.innerHTML = `
                        <div class="promo-success">
                            <p><strong>🎉 ${data.message}</strong></p>
                            <p style="font-size:0.9rem; margin-top:0.4rem;">Present this code at any checkout:</p>
                            <div class="promo-code-pill">${data.promo_code}</div>
                            <p style="font-size:0.8rem; margin-top:0.4rem; color: #cbd5e1;">${data.discount}</p>
                        </div>
                    `;
                    emailInput.value = '';
                } else {
                    promoFeedback.innerHTML = `<span style="color: #ff4444;">${data.message}</span>`;
                }
            } catch (err) {
                promoFeedback.innerHTML = `<span style="color: #ff4444;">Failed to connect to promo server. Please retry.</span>`;
            }
        });
    }

    // ==========================================================
    // 11. AMBIENT BACKGROUND CARBONATION PARTICLES
    // ==========================================================
    const particleCanvas = document.getElementById('particleCanvas');
    if (particleCanvas) {
        const pCtx = particleCanvas.getContext('2d');
        let pWidth = particleCanvas.width = window.innerWidth;
        let pHeight = particleCanvas.height = window.innerHeight;

        window.addEventListener('resize', () => {
            pWidth = particleCanvas.width = window.innerWidth;
            pHeight = particleCanvas.height = window.innerHeight;
        });

        const bubbles = [];
        for (let i = 0; i < 50; i++) {
            bubbles.push({
                x: Math.random() * pWidth,
                y: Math.random() * pHeight,
                radius: Math.random() * 2.8 + 0.6,
                speedY: Math.random() * 1.5 + 0.4,
                opacity: Math.random() * 0.5 + 0.1
            });
        }

        function animateBubbles() {
            pCtx.clearRect(0, 0, pWidth, pHeight);
            const config = flavorConfigs[currentFlavor] || flavorConfigs['mango-loco'];

            bubbles.forEach(b => {
                b.y -= b.speedY;
                if (b.y < -10) {
                    b.y = pHeight + 10;
                    b.x = Math.random() * pWidth;
                }

                pCtx.beginPath();
                pCtx.arc(b.x, b.y, b.radius, 0, Math.PI * 2);
                pCtx.fillStyle = config.primary;
                pCtx.globalAlpha = b.opacity;
                pCtx.fill();
            });

            pCtx.globalAlpha = 1.0;
            requestAnimationFrame(animateBubbles);
        }

        animateBubbles();
    }
});
