        // iOS Font Awesome Fix - Force font loading and redraw
        (function() {
            function fixFontAwesome() {
                if (/iPad|iPhone|iPod/.test(navigator.userAgent) || /Safari/.test(navigator.userAgent)) {
                    // Force redraw of Font Awesome icons
                    const faElements = document.querySelectorAll('[class*="fa-"], .fas, .far, .fab');
                    faElements.forEach(function(el) {
                        // Force font family and weight
                        if (el.classList.contains('fas')) {
                            el.style.fontFamily = '"Font Awesome 5 Free"';
                            el.style.fontWeight = '900';
                        } else if (el.classList.contains('far')) {
                            el.style.fontFamily = '"Font Awesome 5 Free"';
                            el.style.fontWeight = '400';
                        } else if (el.classList.contains('fab')) {
                            el.style.fontFamily = '"Font Awesome 5 Brands"';
                            el.style.fontWeight = '400';
                        }
                        
                        // Force repaint
                        el.style.webkitTransform = 'translateZ(0)';
                        el.style.transform = 'translateZ(0)';
                        el.offsetHeight; // Force reflow
                    });
                }
            }

            // Run on DOMContentLoaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(fixFontAwesome, 100);
                    setTimeout(fixFontAwesome, 500); // Second attempt
                });
            } else {
                setTimeout(fixFontAwesome, 100);
            }

            // Run when page becomes visible (fixes iOS cache issues)
            document.addEventListener('visibilitychange', function() {
                if (!document.hidden) {
                    setTimeout(fixFontAwesome, 50);
                }
            });

            // Run on window focus
            window.addEventListener('focus', function() {
                setTimeout(fixFontAwesome, 50);
            });

            // Run on page show (back/forward cache)
            window.addEventListener('pageshow', function() {
                setTimeout(fixFontAwesome, 50);
            });
        })();