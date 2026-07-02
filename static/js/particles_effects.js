document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('magic-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let W = window.innerWidth;
    let H = window.innerHeight;
    canvas.width = W;
    canvas.height = H;

    // Colores cálidos y dorados para fuegos artificiales de boda
    const colors = ['#d4af37', '#ffffff', '#ffb6c1', '#ffd700', '#ff6b81', '#f9e596'];

    class Firework {
        constructor() {
            this.x = Math.random() * W;
            this.y = H;
            this.targetX = Math.random() * W;
            this.targetY = Math.random() * (H / 2); // Explota en la mitad superior
            this.speed = Math.random() * 2 + 3; // Velocidad de subida
            this.angle = Math.atan2(this.targetY - this.y, this.targetX - this.x);
            this.vx = Math.cos(this.angle) * this.speed;
            this.vy = Math.sin(this.angle) * this.speed;
            this.trail = [];
            this.color = colors[Math.floor(Math.random() * colors.length)];
            this.exploded = false;
        }

        update() {
            this.trail.push({x: this.x, y: this.y});
            if (this.trail.length > 5) this.trail.shift();

            this.x += this.vx;
            this.y += this.vy;

            // Añadir gravedad sutil al cohete
            this.vy += 0.02;

            // Chequear si alcanzó el objetivo (si está bajando)
            if (this.vy >= 0 || this.y <= this.targetY) {
                this.exploded = true;
                this.explode();
            }
        }

        draw() {
            ctx.beginPath();
            if (this.trail.length > 0) {
                ctx.moveTo(this.trail[0].x, this.trail[0].y);
            } else {
                ctx.moveTo(this.x, this.y);
            }
            ctx.lineTo(this.x, this.y);
            ctx.strokeStyle = this.color;
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        explode() {
            const count = Math.random() * 50 + 50; // Cantidad de chispas
            for (let i = 0; i < count; i++) {
                particles.push(new Spark(this.x, this.y, this.color));
            }
        }
    }

    class Spark {
        constructor(x, y, color) {
            this.x = x;
            this.y = y;
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 5 + 1;
            this.vx = Math.cos(angle) * speed;
            this.vy = Math.sin(angle) * speed;
            this.friction = 0.95;
            this.gravity = 0.05;
            this.alpha = 1;
            this.decay = Math.random() * 0.02 + 0.01;
            this.color = color;
        }

        update() {
            this.vx *= this.friction;
            this.vy *= this.friction;
            this.vy += this.gravity;
            this.x += this.vx;
            this.y += this.vy;
            this.alpha -= this.decay;
        }

        draw() {
            ctx.save();
            ctx.globalAlpha = this.alpha;
            ctx.beginPath();
            ctx.arc(this.x, this.y, Math.random() * 2 + 1, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.shadowBlur = 10;
            ctx.shadowColor = this.color;
            ctx.fill();
            ctx.restore();
        }
    }

    let fireworks = [];
    let particles = [];
    let lastLaunch = 0;

    function animate(time) {
        // Efecto estela oscura (fondo transparente)
        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'; // Si dejamos transparente puro, la estela no funciona. Usamos un alpha bajo.
        // Pero dado que el canvas está sobre la imagen de fondo, hacer fillRect negro tapa la imagen de fondo.
        // En su lugar, usamos clearRect y estelas sin difuminar (solo arrays de puntos)
        ctx.clearRect(0, 0, W, H);
        
        // Lanzar un fuego artificial cada cierto tiempo aleatorio (ej. 800ms - 2000ms)
        if (time - lastLaunch > Math.random() * 1500 + 500) {
            fireworks.push(new Firework());
            lastLaunch = time;
        }

        for (let i = fireworks.length - 1; i >= 0; i--) {
            fireworks[i].update();
            fireworks[i].draw();
            if (fireworks[i].exploded) {
                fireworks.splice(i, 1);
            }
        }

        for (let i = particles.length - 1; i >= 0; i--) {
            particles[i].update();
            particles[i].draw();
            if (particles[i].alpha <= 0) {
                particles.splice(i, 1);
            }
        }

        requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);

    window.addEventListener('resize', () => {
        W = window.innerWidth;
        H = window.innerHeight;
        canvas.width = W;
        canvas.height = H;
    });
});
