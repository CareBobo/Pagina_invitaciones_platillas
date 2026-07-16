document.addEventListener('DOMContentLoaded', () => {
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

    let isPortraitMobile = window.innerWidth < window.innerHeight && window.innerWidth <= 768;
    
    let pageW = 350;
    let pageH = 500;

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
        window.pageFlip = new St.PageFlip(flipBookElement, {
            width: pageW,
            height: pageH,
            size: "stretch",
            minWidth: 200,
            maxWidth: 600,
            minHeight: 280,
            maxHeight: 850,
            drawShadow: true,
            showCover: true,
            usePortrait: isPortraitMobile, 
            mobileScrollSupport: false,
            maxShadowOpacity: 0.5,
            flippingTime: 1000
        });

        const pages = document.querySelectorAll('.page');
        window.pageFlip.loadFromHTML(pages);

        flipBookElement.classList.add('closed-scale-front');
        flipBookElement.style.display = 'block';

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
            flipBookElement.classList.remove('closed-scale-front', 'closed-scale-back', 'book-open-scale');

            if (e.data === 0) {
                flipBookElement.classList.add('closed-scale-front');
                if (swipeHint) {
                    swipeHint.style.display = 'flex';
                    setTimeout(() => swipeHint.classList.remove('hidden'), 50);
                }
            } else if (e.data === totalPages - 1) {
                flipBookElement.classList.add('closed-scale-back');
                setTimeout(() => {
                    window.pageFlip.flip(0);
                }, 1500);
            } else {
                flipBookElement.classList.add('book-open-scale');
            }

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