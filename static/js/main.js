/* ==========================================================================
   LÓGICA GENERAL DE LA INVITACIÓN PREMIUM - MAIN.JS
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Activar el modo JS en el body para animaciones progresivas
    document.body.classList.add('js-enabled');

    try {
        // Registrar el Plugin de ScrollTrigger para GSAP si está cargado
        if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
            gsap.registerPlugin(ScrollTrigger);
            initGsapAnimations();
        } else {
            // Fallback: Intersection Observer si GSAP no está cargado
            initIntersectionObserver();
        }
    } catch (error) {
        console.error("Error al inicializar animaciones, ejecutando fallback de visibilidad:", error);
        showAllElementsFallback();
    }

    // Inicializar componentes
    try {
        initCountdown();
        initAudioPlayer();
        initRSVPForm();
    } catch (error) {
        console.error("Error al inicializar componentes interactivos:", error);
    }
});

// Función de salvaguarda para mostrar todos los elementos en caso de error
function showAllElementsFallback() {
    const reveals = document.querySelectorAll('.reveal, .timeline-item');
    reveals.forEach((el) => {
        el.classList.add('active');
        el.style.opacity = '1';
        el.style.transform = 'translate(0, 0)';
    });
}

// 1. REPRODUCTOR DE AUDIO CON PERSISTENCIA Y AUTOPLAY DESDE SOBRE
function initAudioPlayer() {
    const audio = document.getElementById('bg-audio');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const musicIcon = document.getElementById('music-icon');
    const musicBars = document.getElementById('music-bars');

    if (!playPauseBtn || !audio) return;

    // Detectar si viene desde el sobre (el usuario ya interactuó, autoplay permitido)
    const urlParams = new URLSearchParams(window.location.search);
    const cameFromEnvelope = urlParams.get('autoplay') === '1';

    // Guardar en localStorage para persistencia entre páginas
    if (cameFromEnvelope) {
        localStorage.setItem('music_playing', 'true');
    }

    const musicState = localStorage.getItem('music_playing');

    if (cameFromEnvelope || musicState === 'true') {
        // Intentar reproducir inmediatamente (el usuario ya interactuó en el sobre)
        audio.play().then(() => {
            setPlayingState(true);
        }).catch(err => {
            console.log("Autoplay bloqueado por el navegador.");
            setPlayingState(false);
        });
    }

    playPauseBtn.addEventListener('click', () => {
        if (audio.paused) {
            audio.play().then(() => {
                setPlayingState(true);
            }).catch(err => console.log("Error al reproducir audio:", err));
        } else {
            audio.pause();
            setPlayingState(false);
        }
    });

    // Auto-reproducir al primer click en la página si estaba activo
    document.body.addEventListener('click', () => {
        if (audio.paused && localStorage.getItem('music_playing') === 'true') {
            audio.play().then(() => {
                setPlayingState(true);
            }).catch(e => console.log(e));
        }
    }, { once: true });

    function setPlayingState(playing) {
        if (playing) {
            musicIcon.classList.remove('fa-play');
            musicIcon.classList.add('fa-pause');
            musicBars.classList.add('playing');
            localStorage.setItem('music_playing', 'true');
        } else {
            musicIcon.classList.remove('fa-pause');
            musicIcon.classList.add('fa-play');
            musicBars.classList.remove('playing');
            localStorage.setItem('music_playing', 'false');
        }
    }
}

// 2. CUENTA REGRESIVA DINÁMICA
function initCountdown() {
    const dSpan = document.getElementById('days');
    const hSpan = document.getElementById('hours');
    const mSpan = document.getElementById('minutes');
    const sSpan = document.getElementById('seconds');

    if (!dSpan || typeof eventDate === 'undefined') return;

    function updateTimer() {
        const now = new Date().getTime();
        const difference = eventDate - now;

        if (difference < 0) {
            clearInterval(timerInterval);
            dSpan.innerHTML = "00";
            hSpan.innerHTML = "00";
            mSpan.innerHTML = "00";
            sSpan.innerHTML = "00";
            return;
        }

        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((difference % (1000 * 60)) / 1000);

        dSpan.innerHTML = days < 10 ? '0' + days : days;
        hSpan.innerHTML = hours < 10 ? '0' + hours : hours;
        mSpan.innerHTML = minutes < 10 ? '0' + minutes : minutes;
        sSpan.innerHTML = seconds < 10 ? '0' + seconds : seconds;
    }

    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
}

// 3. LIGHTBOX DE LA GALERÍA MASONRY
function openLightbox(src) {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    if (lightbox && lightboxImg) {
        lightboxImg.src = src;
        lightbox.style.display = 'flex';
        setTimeout(() => {
            lightbox.classList.add('active');
        }, 10);
    }
}

function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.classList.remove('active');
        setTimeout(() => {
            lightbox.style.display = 'none';
        }, 300);
    }
}

// 4. ANIMACIONES PREMIUM GSAP CON SCROLLTRIGGER
function initGsapAnimations() {
    // Animación de aparición de flores y pétalos flotantes
    gsap.from(".floral-header", {
        opacity: 0,
        scale: 0.85,
        duration: 1.5,
        ease: "power2.out",
        scrollTrigger: {
            trigger: ".floral-header",
            start: "top 85%",
            toggleActions: "play none none none"
        }
    });

    // Efecto de aparición para las cards generales
    gsap.utils.toArray(".reveal").forEach((element) => {
        gsap.from(element, {
            opacity: 0,
            y: 40,
            duration: 1.2,
            ease: "power3.out",
            scrollTrigger: {
                trigger: element,
                start: "top 88%",
                toggleActions: "play none none none"
            }
        });
    });

    // Animación secuencial en la línea de tiempo (Cronograma)
    gsap.utils.toArray(".timeline-item").forEach((item, index) => {
        const xOffset = index % 2 === 0 ? -50 : 50;
        gsap.from(item, {
            opacity: 0,
            x: xOffset,
            duration: 1.0,
            ease: "power2.out",
            scrollTrigger: {
                trigger: item,
                start: "top 85%",
                toggleActions: "play none none none"
            }
        });
    });
}

// Fallback: Intersection Observer si GSAP falla o no se carga
function initIntersectionObserver() {
    const reveals = document.querySelectorAll('.reveal, .timeline-item');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });

    reveals.forEach((reveal) => {
        observer.observe(reveal);
    });
}

// 5. FORMULARIO RSVP INTEGRADO CON AJAX Y WHATSAPP
function initRSVPForm() {
    const form = document.getElementById('rsvp-form');
    const statusSelect = document.getElementById('rsvp-status');
    const cuposGroup = document.getElementById('cupos-confirmados-group');
    const alertDiv = document.getElementById('rsvp-alert');
    const whatsappBtn = document.getElementById('rsvp-whatsapp-btn');

    if (!form) return;

    // Mostrar/ocultar selector de asistentes de acuerdo al estado
    if (statusSelect && cuposGroup) {
        statusSelect.addEventListener('change', () => {
            if (statusSelect.value === 'Rechazado') {
                cuposGroup.style.display = 'none';
            } else {
                cuposGroup.style.display = 'block';
            }
        });
    }

    // Envío del RSVP vía AJAX (Fetch)
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const submitBtn = document.getElementById('rsvp-submit-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Enviando...';

        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });

        // Forzar cupos confirmados a 0 si no asiste
        if (data.estado_rsvp === 'Rechazado') {
            data.cupos_confirmados = 0;
        }

        fetch('/invitacion/confirmar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(res => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Guardar RSVP';
            
            if (alertDiv) {
                alertDiv.style.display = 'block';
                if (res.success) {
                    alertDiv.style.backgroundColor = '#d4edda';
                    alertDiv.style.color = '#155724';
                    alertDiv.innerHTML = '¡Respuesta registrada con éxito! Gracias por confirmar.';
                } else {
                    alertDiv.style.backgroundColor = '#f8d7da';
                    alertDiv.style.color = '#721c24';
                    alertDiv.innerHTML = 'Ocurrió un error: ' + res.message;
                }
            }
        })
        .catch(err => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Guardar RSVP';
            console.error(err);
            if (alertDiv) {
                alertDiv.style.display = 'block';
                alertDiv.style.backgroundColor = '#f8d7da';
                alertDiv.style.color = '#721c24';
                alertDiv.innerHTML = 'Error de conexión. Inténtalo de nuevo.';
            }
        });
    });

    // Lógica para formatear y abrir enlace de WhatsApp
    if (whatsappBtn) {
        whatsappBtn.addEventListener('click', () => {
            const nombre = form.querySelector('[name="nombre"]').value;
            const telefono = form.querySelector('[name="telefono"]').value;
            const estado = statusSelect.value;
            const cupos = form.querySelector('[name="cupos_confirmados"]') ? form.querySelector('[name="cupos_confirmados"]').value : 0;
            const mensaje = form.querySelector('[name="mensaje_rsvp"]').value;

            // Número configurado en el backend
            const whatsappNumber = "{{ invitacion.whatsapp_confirmacion }}"; 

            let text = `Hola! Soy *${nombre}*. Confirmo mi asistencia al evento:\n\n`;
            if (estado === 'Confirmado') {
                text += `✅ *Sí, asistiré*\n`;
                text += `👥 *Asistentes:* ${cupos} persona(s)\n`;
            } else {
                text += `❌ *No podré asistir*\n`;
            }
            if (mensaje.trim()) {
                text += `✉️ *Mensaje:* ${mensaje}\n`;
            }
            if (telefono.trim()) {
                text += `📱 *Contacto:* ${telefono}`;
            }

            const encodedText = encodeURIComponent(text);
            
            // Si hay número configurado, enviar directamente. Si no, abrir sin número destinatario para que el invitado elija
            const url = whatsappNumber && whatsappNumber !== 'None'
                ? `https://api.whatsapp.com/send?phone=${whatsappNumber}&text=${encodedText}`
                : `https://api.whatsapp.com/send?text=${encodedText}`;

            window.open(url, '_blank');
        });
    }
}
