/* ==========================================================================
   INTERACCIONES 3D DEL SOBRE DE INVITACIÓN - ENVELOPE.JS
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const envelopeContainer = document.getElementById('envelope-container');
    const envelopeWrapper = document.getElementById('envelope-wrapper');
    const envelopeSeal = document.getElementById('envelope-seal');
    const entryBtnContainer = document.getElementById('entry-btn-container');

    let isOpen = false;

    // 1. EFECTO PARALLAX 3D CON EL MOUSE
    if (envelopeContainer && envelopeWrapper) {
        envelopeContainer.addEventListener('mousemove', (e) => {
            if (isOpen) return; // Detener efecto si ya está abierto

            const rect = envelopeContainer.getBoundingClientRect();
            // Calcular posiciones del cursor relativas al centro del contenedor del sobre
            const x = e.clientX - rect.left - (rect.width / 2);
            const y = e.clientY - rect.top - (rect.height / 2);

            // Convertir a grados de rotación suave (máximo 15 grados)
            const rotateX = -(y / (rect.height / 2)) * 12;
            const rotateY = (x / (rect.width / 2)) * 15;

            envelopeWrapper.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        // Restaurar posición cuando el mouse sale
        envelopeContainer.addEventListener('mouseleave', () => {
            if (isOpen) return;
            envelopeWrapper.style.transform = 'rotateX(0deg) rotateY(0deg)';
        });
    }

    // 2. FUNCIÓN PARA ABRIR EL SOBRE
    function openEnvelope() {
        if (isOpen) return;
        isOpen = true;

        // Quitar efectos interactivos del mouse y centrar el sobre
        envelopeWrapper.style.transform = 'rotateX(0deg) rotateY(0deg) scale(1.05)';
        
        setTimeout(() => {
            // Activar clase CSS para la animación cinematográfica
            envelopeWrapper.classList.add('open');
            
            // Sonido de papel al abrirse (opcional, reproducido si el audio del reproductor se inicia)
            const bgAudio = document.getElementById('bg-audio');
            if (bgAudio && bgAudio.paused) {
                bgAudio.play().catch(err => console.log("Audio autoplay prevenido:", err));
                
                // Actualizar UI del reproductor flotante
                const musicIcon = document.getElementById('music-icon');
                const musicBars = document.getElementById('music-bars');
                if (musicIcon && musicBars) {
                    musicIcon.classList.remove('fa-play');
                    musicIcon.classList.add('fa-pause');
                    musicBars.classList.add('playing');
                }
            }

            // Ocultar el nameplate al abrir el sobre
            const nameplate = document.getElementById('guest-nameplate');
            if (nameplate) {
                nameplate.style.opacity = '0';
                nameplate.style.transform = 'translateY(15px)';
                nameplate.style.pointerEvents = 'none';
            }

            // Mostrar el botón de entrada después de que la carta haya salido completamente (aprox. 1.2s)
            setTimeout(() => {
                entryBtnContainer.classList.add('show');
            }, 1200);
            
        }, 300);
    }

    // 3. EVENTOS DE ACTIVACIÓN (CLICK EN SELLO O EN TODO EL SOBRE)
    if (envelopeSeal) {
        envelopeSeal.addEventListener('click', (e) => {
            e.stopPropagation(); // Evitar doble evento
            openEnvelope();
        });
    }

    if (envelopeWrapper) {
        envelopeWrapper.addEventListener('click', () => {
            openEnvelope();
        });
    }
});
