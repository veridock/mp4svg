/**
 * SVG Video Player Initialization
 */

// Initialize the player when the SVG loads
function initBase91Player() {
    const statusElement = document.getElementById('status-message');
    const video = document.getElementById('svg-video-player');
    
    if (!statusElement || !video) {
        console.error('Required elements not found');
        return;
    }
    
    try {
        // Get the Base91 data from the script tag
        const dataScript = document.getElementById('base91-video-data');
        if (!dataScript) {
            throw new Error('Video data not found');
        }
        
        const base91Data = dataScript.textContent.trim();
        if (!base91Data) {
            throw new Error('No video data available');
        }
        
        statusElement.textContent = 'Decoding video data...';
        
        // Small delay to allow UI to update
        setTimeout(() => {
            try {
                // Decode the Base91 data
                const base91 = new Base91();
                const uint8Array = base91.decode(base91Data);
                
                // Create a Blob URL for the video
                const blob = new Blob([uint8Array], {type: 'video/mp4'});
                const videoUrl = URL.createObjectURL(blob);
                
                // Set up the video element
                video.src = videoUrl;
                video.style.display = 'block';
                statusElement.style.display = 'none';
                
                // Try to autoplay (may be blocked by browser policy)
                const playPromise = video.play();
                
                if (playPromise !== undefined) {
                    playPromise.catch(error => {
                        console.log('Autoplay prevented:', error);
                        statusElement.textContent = 'Click to play (autoplay blocked)';
                        statusElement.style.display = 'block';
                        video.controls = true;
                    });
                }
                
                // Handle video errors
                video.onerror = function() {
                    statusElement.textContent = 'Error loading video';
                    statusElement.style.display = 'block';
                    console.error('Video loading error');
                };
                
            } catch (e) {
                statusElement.textContent = 'Error: ' + e.message;
                statusElement.style.display = 'block';
                console.error('Player error:', e);
            }
        }, 100);
        
    } catch (e) {
        statusElement.textContent = 'Error: ' + e.message;
        statusElement.style.display = 'block';
        console.error('Initialization error:', e);
    }
}

// Toggle fullscreen mode
function toggleFullScreen() {
    const video = document.getElementById('svg-video-player');
    if (!video) return;
    
    if (!document.fullscreenElement) {
        if (video.requestFullscreen) {
            video.requestFullscreen();
        } else if (video.webkitRequestFullscreen) { /* Safari */
            video.webkitRequestFullscreen();
        } else if (video.msRequestFullscreen) { /* IE11 */
            video.msRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) { /* Safari */
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) { /* IE11 */
            document.msExitFullscreen();
        }
    }
}

// Initialize when the SVG is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBase91Player);
} else {
    // DOM already loaded, initialize immediately
    initBase91Player();
}
