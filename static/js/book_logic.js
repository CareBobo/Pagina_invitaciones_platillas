document.addEventListener('DOMContentLoaded', () => {
    // Override prototype methods to prevent premature update/resize crashes
    if (window.St && window.St.PageFlip) {
        St.PageFlip.prototype.getRender = function () {
            return this.render || { update: () => { } };
        };
        const originalUpdate = St.PageFlip.prototype.update;
        St.PageFlip.prototype.update = function () {
            if (this.render && this.pages) {
                originalUpdate.apply(this);
            }
        };
    }

    const flipBookElement = document.getElementById('flip-book');
    const mainContainer = document.getElementById('main-container');
    const audio = document.getElementById('bg-music');
    const btnMusic = document.getElementById('music-toggle');
    const swipeHint = document.getElementById('swipe-hint');
    const stickerInventory = document.getElementById('sticker-inventory');
    const toggleBtn = document.getElementById('toggle-inventory-btn');
    const closeBtn = document.getElementById('close-inventory-btn');

    let isMusicPlaying = false;
    let musicStarted = false;

    // Ya no usamos isPortraitMobile para el libro, siempre mostramos 2 páginas (usePortrait: false)
    // porque en celulares forzamos al usuario a rotar a landscape (horizontal)

    let pageW = 450;
    let pageH = 650;

    let pageFlip;

    mainContainer.style.display = 'flex';
    initBook();

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

        // Make the element visible before initializing PageFlip to ensure correct dimensions
        flipBookElement.style.display = 'block';

        window.pageFlip = new St.PageFlip(flipBookElement, {
            width: pageW,
            height: pageH,
            size: "stretch",
            minWidth: 100,
            maxWidth: 2000,
            minHeight: 100,
            maxHeight: 2000,
            drawShadow: true,
            showCover: true,
            usePortrait: false, // Siempre 2 páginas en formato horizontal
            mobileScrollSupport: false,
            maxShadowOpacity: 0.5,
            flippingTime: 1000,
            autoCenter: false
        });

        const pages = document.querySelectorAll('.page');
        window.pageFlip.loadFromHTML(pages);

        // Initial resize
        resizeBook();

        // Allow opening the book by clicking/tapping anywhere on the closed cover
        flipBookElement.addEventListener('click', (e) => {
            if (window.pageFlip) {
                // Prevenir doble-salto si la librería ya está animando la página
                if (window.pageFlip.getState() === 'flipping') return;

                const currentPage = window.pageFlip.getCurrentPageIndex();
                if (currentPage === 0) {
                    window.pageFlip.flipNext();
                }
            }
        });

        flipBookElement.addEventListener('pointerdown', () => {
            if (swipeHint && !swipeHint.classList.contains('hidden')) {
                swipeHint.classList.add('hidden');
                setTimeout(() => swipeHint.style.display = 'none', 500);
            }
        });

        window.pageFlip.on('flip', (e) => {
            if (swipeHint) {
                swipeHint.classList.add('hidden');
                setTimeout(() => swipeHint.style.display = 'none', 500);
            }

            const totalPages = window.pageFlip.getPageCount();

            const menuBtn = document.getElementById('btn-index-bottom');

            if (e.data === 0) {
                if (swipeHint) {
                    swipeHint.style.display = 'flex';
                    setTimeout(() => swipeHint.classList.remove('hidden'), 50);
                }
                if (menuBtn) {
                    menuBtn.classList.remove('open-book-menu');
                }
            } else if (e.data === totalPages - 1) {
                if (swipeHint) {
                    swipeHint.style.display = 'none';
                }
                if (menuBtn) {
                    menuBtn.classList.remove('open-book-menu');
                }
            } else {
                if (swipeHint) {
                    swipeHint.style.display = 'none';
                }
                if (menuBtn) {
                    menuBtn.classList.add('open-book-menu');
                }
            }

            // Force dynamic resizing to smoothly animate scaling between open/closed states
            resizeBook(e.data);

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
                    mainVideo.muted = false;
                    mainVideo.volume = 0.1;
                    mainVideo.play().catch(e => console.log(e));
                }
            }
        });
    }

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

    const stopPropagation = (e) => e.stopPropagation();

    const blockFlipOnElements = () => {
        document.querySelectorAll('input, select, button, video, a, .zoomable, .content-box').forEach(el => {
            const events = ['pointerdown', 'pointerup', 'touchstart', 'touchend', 'mousedown', 'mouseup', 'click'];
            events.forEach(eventType => {
                el.removeEventListener(eventType, stopPropagation);
                el.addEventListener(eventType, stopPropagation, { passive: false });
            });
        });
    };

    setTimeout(blockFlipOnElements, 500);

    const mainVideo = document.getElementById('main-video');
    if (mainVideo) {
        mainVideo.addEventListener('pointerdown', (e) => {
            e.stopPropagation();
        });
    }
});
function resizeBook(targetPage) {
    let isOpen = false;
    let currentPage = 0;
    let totalPages = 0;

    if (window.pageFlip) {
        currentPage = typeof targetPage === 'number' ? targetPage : window.pageFlip.getCurrentPageIndex();
        totalPages = window.pageFlip.getPageCount();
        if (currentPage > 0 && currentPage < totalPages - 1) {
            isOpen = true;
        }
    }

    // Calculamos el tamaño usando SIEMPRE el factor del libro abierto. 
    // Así la caja no cambia de tamaño real y evitamos que las páginas se partan.
    let availableW = window.innerWidth * 0.98; 
    let availableH = window.innerHeight * 0.82; 
    
    // Queremos mantener la proporción 900:650
    let baseScale = Math.min(availableW / 900, availableH / 650);
    
    let targetW = 900 * baseScale;
    let targetH = 650 * baseScale;
    
    let wrapper = document.querySelector('.book-3d-wrapper');
    if (wrapper) {
        // Fijamos el tamaño estático
        wrapper.style.width = targetW + 'px';
        wrapper.style.height = targetH + 'px';
        wrapper.style.maxWidth = 'none';
        wrapper.style.maxHeight = 'none';

        // Definimos la escala (el zoom) dependiendo de si está abierto o cerrado
        let scaleFactor = isOpen ? 1 : 0.85;

        // Calculamos el 25% exacto en píxeles (evita bugs del navegador al cargar la página)
        let offset = targetW * 0.25;

        // Aplicamos centrado Y la escala de tamaño al mismo tiempo
        if (window.pageFlip) {
            if (currentPage === 0) {
                // Portada
                wrapper.style.transform = `rotateX(5deg) translateX(-${offset}px) scale(${scaleFactor})`;
            } else if (currentPage === totalPages - 1 && totalPages > 0) {
                // Contraportada
                wrapper.style.transform = `rotateX(5deg) translateX(${offset}px) scale(${scaleFactor})`;
            } else {
                // Abierto
                wrapper.style.transform = `rotateX(5deg) translateX(0px) scale(${scaleFactor})`;
            }
        } else {
            wrapper.style.transform = `rotateX(5deg) translateX(-${offset}px) scale(${scaleFactor})`;
        }

        // Animamos SOLAMENTE el transform (movimiento y escala), no el width/height.
        wrapper.style.transition = 'transform 0.4s ease-out';
    }
    
    let flipBook = document.getElementById('flip-book');
    if (flipBook) {
        flipBook.style.fontSize = (16 * Math.max(baseScale, 0.4)) + 'px';
    }
    
    if (window.pageFlip) {
        try {
            window.pageFlip.update();
        } catch (e) {
            console.warn("Could not update pageFlip:", e);
        }
    }
}
window.addEventListener('resize', resizeBook);
