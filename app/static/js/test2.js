const nav = document.getElementById('main-nav');
        let lastScrollTop = 0;

        window.addEventListener('scroll', function() {
            let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > nav.offsetHeight) {
                nav.classList.add('hidden');
            } else {
                nav.classList.remove('hidden');
            }
            
            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        });

        const menuToggle = document.getElementById('menu-toggle-button');
        const fullscreenMenu = document.getElementById('fullscreen-menu');
        const body = document.body;

        menuToggle.addEventListener('click', () => {
            body.classList.toggle('overflow-hidden');
            fullscreenMenu.classList.toggle('active');
        });

        document.addEventListener('DOMContentLoaded', () => {
            const contentGrid = document.getElementById('main-content-grid');
            const contentColumn = document.getElementById('content-column');
            const cardGroups = document.querySelectorAll('.card-group');
            const stickyCards = document.querySelectorAll('.sticky-card-wrapper');
            const backgroundColors = {
                '1': 'var(--color-teal-300)',
                '2': 'var(--color-orange-300)',
                '3': 'var(--color-violet-300)'
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const sectionId = entry.target.dataset.sectionId;
                        const layout = entry.target.dataset.layout;

                        // Update sticky card visibility
                        stickyCards.forEach(card => {
                            if (card.id === `sticky-card-${sectionId}`) {
                                card.classList.add('is-active');
                            } else {
                                card.classList.remove('is-active');
                            }
                        });
                        
                        // Update background color
                        contentColumn.style.backgroundColor = backgroundColors[sectionId];
                        
                        // Update grid layout
                        if (layout === 'reverse') {
                            contentGrid.classList.add('layout-reverse');
                        } else {
                            contentGrid.classList.remove('layout-reverse');
                        }

                         // Animate in cards
                        entry.target.classList.add('is-visible');

                    }
                });
            }, { threshold: 0.4 });

            cardGroups.forEach(group => {
                observer.observe(group);
            });

            // Set initial state
            if (cardGroups.length > 0) {
                 contentColumn.style.backgroundColor = backgroundColors['1'];
                 document.getElementById('sticky-card-1').classList.add('is-active');
            }
        });