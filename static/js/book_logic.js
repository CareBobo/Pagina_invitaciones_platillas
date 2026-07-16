document.addEventListener('DOMContentLoaded', () => {
    const flipBookElement = document.getElementById('flip-book');
    const mainContainer = document.getElementById('main-container');
    const audio = document.getElementById('bg-music');
    const btnMusic = document.getElementById('music-toggle');
    const swipeHint = document.getElementById('swipe-hint');

    // Elementos del Inventario
    const stickerInventory = document.getElementById('sticker-inventory');
    const toggleBtn = document.getElementById('toggle-inventory-btn');
    const closeBtn = document.getElementById('close-inventory-btn');

    let isMusicPlaying = false;
    let musicStarted = false;

    // Calcular dimensiones base del libro (aspect ratio)
    // En móviles verticales queremos que sea casi todo el ancho, en apaisado queremos que se vea completo.
    let isPortraitMobile = window.innerWidth < window.innerHeight && window.innerWidth <= 768;
    
    // El tamaño base del libro. Al usar size: "fit", el libro se escalará para caber siempre en la pantalla
    // manteniendo esta proporción (ej. 350x500 = aspecto 7:10).
    let pageW = 350;
    let pageH = 500;

    // Inicializar stPageFlip
    let pageFlip;

    // Mostrar el libro inmediatamente
    mainContainer.style.display = 'flex';
    initBook();

    // Toggle Inventario
    if (toggleBtn && closeBtn) {
        toggleBtn.addEventListener('click', () => {
            stickerInventory.style.display = 'flex';
            setTimeout(() => stickerInventory.classList.add('visible'), 50);
            toggleBtn.style.display = 'none';
        });

        closeBtn.addEventListener('click', () => {
            stickerInventory.classList.remove('visible');
            setTimeout(() => {
                stickerInventory.style.display = 'none';
                toggleBtn.style.display = 'block';
            }, 500);
        });
    }

    function initBook() {
        if (window.pageFlip) return;
        window.pageFlip = new St.PageFlip(flipBookElement, {
            width: pageW,
            height: pageH,
            size: "fit", // 'fit' garantiza que nunca se corte, siempre se ajusta al tamaño de la pantalla
            minWidth: 200,
            maxWidth: 600,
            minHeight: 280,
            maxHeight: 850,
            drawShadow: true,
            showCover: true,
            usePortrait: isPortraitMobile, // En horizontal (landscape) se verán 2 páginas como la segunda foto
            mobileScrollSupport: false,
            maxShadowOpacity: 0.5,
            flippingTime: 1000
        });

        const pages = document.querySelectorAll('.page');
        window.pageFlip.loadFromHTML(pages);

        // El libro empieza pequeño (cerrado)
        flipBookElement.classList.add('closed-scale-front');
        flipBookElement.style.display = 'block';

        // Ocultar swipeHint al tocar
        flipBookElement.addEventListener('pointerdown', () => {
            if (swipeHint && !swipeHint.classList.contains('hidden')) {
                swipeHint.classList.add('hidden');
                setTimeout(() => swipeHint.style.display = 'none', 500);
            }
        });

        // Evento al pasar página para controlar el tamaño y música
        window.pageFlip.on('flip', (e) => {
            // Ocultar hint
            if (swipeHint) {
                swipeHint.classList.add('hidden');
                setTimeout(() => swipeHint.style.display = 'none', 500);
            }

            const totalPages = window.pageFlip.getPageCount();
            flipBookElement.classList.remove('closed-scale-front', 'closed-scale-back');

            // Si está en la portada (página 0), centrar y achicar
            if (e.data === 0) {
                flipBookElement.classList.add('closed-scale-front');
                // Si está en la contraportada (libro totalmente cerrado al final)
            } else if (e.data === totalPages - 1) {
                flipBookElement.classList.add('closed-scale-back');

                // Regresar a la portada sin hacer giros 3D extremos
                setTimeout(() => {
                    window.pageFlip.flip(0); // Ir a página 0
                }, 1500);
            }

            // Iniciar música y video en la primera interacción
            if (!musicStarted && audio) {
                audio.play().then(() => {
                    isMusicPlaying = true;
                    musicStarted = true;
                    if (btnMusic) {
                        btnMusic.style.display = 'flex';
                        btnMusic.innerHTML = '<i class="fas fa-volume-up"></i>';
                    }
                }).catch(err => console.log("Autoplay bloqueado"));

                const mainVideo = document.getElementById('main-video');
                if (mainVideo) {
                    mainVideo.muted = false; // desmutear para que se escuche bajito
                    mainVideo.volume = 0.1; // Volumen bajito
                    mainVideo.play().catch(e => console.log(e));
                }
            }
        });
    }

    // Control manual de música
    if (btnMusic && audio) {
        btnMusic.addEventListener('click', () => {
            if (audio.paused) {
                audio.play();
                btnMusic.innerHTML = '<i class="fas fa-volume-up"></i>';
            } else {
                audio.pause();
                btnMusic.innerHTML = '<i class="fas fa-volume-mute"></i>';
            }
        });
    }

    // Ya no hay lógica de drag and drop táctil (Cromos eliminados)

    // --- LIGHTBOX Y CONTROL DE VOLTEO DE PÁGINAS ---
    // Detener propagación en elementos interactivos para que stPageFlip no reaccione
    const stopPropagation = (e) => e.stopPropagation();

    // Aplicar a todos los elementos interactivos actuales y futuros (delegación no, asignación directa)
    const blockFlipOnElements = () => {
        document.querySelectorAll('input, select, button, video, a, .zoomable, .content-box').forEach(el => {
            const events = ['pointerdown', 'pointerup', 'touchstart', 'touchend', 'mousedown', 'mouseup', 'click'];
            events.forEach(eventType => {
                el.removeEventListener(eventType, stopPropagation);
                el.addEventListener(eventType, stopPropagation, { passive: false });
            });
        });
    };

    // Ejecutar inicial
    blockFlipOnElements();

    // Lógica para abrir Lightbox
    const lightboxModal = document.getElementById('lightbox-modal');
    const lightboxContent = document.getElementById('lightbox-content');
    const lightboxClose = document.getElementById('lightbox-close');

    if (lightboxModal) {
        lightboxClose.addEventListener('click', () => {
            lightboxModal.style.display = 'none';
            lightboxContent.innerHTML = ''; // Limpiar contenido para pausar video
            const mainVideo = document.getElementById('main-video');
            if (mainVideo) {
                mainVideo.muted = false;
                mainVideo.volume = 0.1;
            }
        });

        // Cerrar al tocar fuera de la imagen
        lightboxModal.addEventListener('click', (e) => {
            if (e.target === lightboxModal) {
                lightboxModal.style.display = 'none';
                lightboxContent.innerHTML = '';
                const mainVideo = document.getElementById('main-video');
                if (mainVideo) {
                    mainVideo.muted = false;
                    mainVideo.volume = 0.1;
                }
            }
        });

        document.querySelectorAll('.zoomable').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                lightboxModal.style.display = 'flex';

                if (el.tagName.toLowerCase() === 'img') {
                    lightboxContent.innerHTML = `<img src="${el.src}" style="max-width: 100%; max-height: 85vh; border: 4px solid #d4af37; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); object-fit: contain;">`;
                } else if (el.tagName.toLowerCase() === 'video') {
                    if (el.id === 'main-video') el.volume = 0; // mutear el pequeño
                    lightboxContent.innerHTML = `<video src="${el.src}" controls autoplay playsinline style="max-width: 100%; max-height: 85vh; border: 4px solid #d4af37; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); object-fit: contain;"></video>`;
                }
            });
        });
    }

    // --- Cuentas y Forms básicos (Mantenemos los que estaban en el libro normal) ---
    const dateInput = document.getElementById('event-date');
    if (dateInput) {
        const countDownDate = new Date(dateInput.value).getTime();
        const countdownInterval = setInterval(() => {
            const now = new Date().getTime();
            const distance = countDownDate - now;
            if (distance < 0) {
                clearInterval(countdownInterval);
                return;
            }
            document.getElementById("cd-days").innerHTML = Math.floor(distance / (1000 * 60 * 60 * 24)).toString().padStart(2, '0');
            document.getElementById("cd-hours").innerHTML = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)).toString().padStart(2, '0');
            document.getElementById("cd-mins").innerHTML = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)).toString().padStart(2, '0');
            document.getElementById("cd-secs").innerHTML = Math.floor((distance % (1000 * 60)) / 1000).toString().padStart(2, '0');
        }, 1000);
    }
});
