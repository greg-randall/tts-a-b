document.addEventListener('DOMContentLoaded', () => {
    // --- Audio Player Logic ---
    let currentlyPlaying = null;
    const allAudios = document.querySelectorAll('.voice-audio');
    const playButtons = document.querySelectorAll('.play-button');
    const timeDisplay = document.getElementById('currentTime');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const timeSlider = document.querySelector('#timeSlider input');
    const repeatMsInput = document.getElementById('repeatMs');
    const loopToggle = document.getElementById('loopToggle');
    let isDragging = false;

    // These should be set in the HTML via data attributes or global vars if needed
    const autoPlayVoice = document.body.dataset.autoPlayVoice;
    const randomStartPercent = parseFloat(document.body.dataset.randomStartPercent || 0);

    if (autoPlayVoice) {
        const audioToPlay = document.querySelector(`.voice-audio[data-voice="${autoPlayVoice}"]`);
        if (audioToPlay) {
            audioToPlay.addEventListener('loadedmetadata', () => {
                const randomStartTime = (randomStartPercent / 100) * audioToPlay.duration;
                audioToPlay.currentTime = randomStartTime;
                currentlyPlaying = audioToPlay;
                audioToPlay.play();
                updatePlayState();
            }, { once: true });
        }
    }

    function updatePlayState() {
        if (playPauseBtn) {
            playPauseBtn.textContent = (!currentlyPlaying || currentlyPlaying.paused) ? '▶️' : '⏸️';
        }
        
        playButtons.forEach(button => {
            const voiceLabel = button.getAttribute('data-voice');
            const audio = document.querySelector(`.voice-audio[data-voice="${voiceLabel}"]`);
            const isCompact = button.hasAttribute('data-compact');
            
            if (currentlyPlaying === audio && !audio.paused) {
                button.innerHTML = '<i class="fas fa-pause"></i> Pause';
                button.classList.add('playing');
            } else {
                if (isCompact) {
                    button.innerHTML = '<i class="fas fa-play"></i> Play';
                } else {
                    button.innerHTML = `<i class="fas fa-play"></i> Play Voice ${voiceLabel}`;
                }
                button.classList.remove('playing');
            }
        });
    }

    function updateTimeDisplay(e) {
        if (e.target === currentlyPlaying && !isDragging && timeDisplay && timeSlider) {
            const currentProgress = (e.target.currentTime / e.target.duration) * 100;
            const minutes = Math.floor(e.target.currentTime / 60);
            const seconds = Math.floor(e.target.currentTime % 60).toString().padStart(2, '0');
            timeDisplay.textContent = `${minutes}:${seconds}`;
            timeSlider.value = currentProgress;
        }
    }

    function togglePlayPause() {
        if (!currentlyPlaying && allAudios.length > 0) {
            currentlyPlaying = allAudios[0];
        }

        if (currentlyPlaying) {
            if (currentlyPlaying.paused) {
                currentlyPlaying.play();
            } else {
                currentlyPlaying.pause();
            }
            updatePlayState();
        }
    }

    allAudios.forEach(audio => {
        audio.addEventListener('timeupdate', updateTimeDisplay);

        audio.addEventListener('ended', () => {
            if (loopToggle && loopToggle.checked) {
                const repeatDelay = parseInt(repeatMsInput.value || 250);
                setTimeout(() => {
                    if (audio === currentlyPlaying) {
                        audio.currentTime = 0;
                        audio.play();
                    }
                }, repeatDelay);
            } else {
                audio.currentTime = 0;
                updatePlayState();
            }
        });
    });

    playButtons.forEach(button => {
        button.addEventListener('click', () => {
            const voiceLabel = button.getAttribute('data-voice');
            const audio = document.querySelector(`.voice-audio[data-voice="${voiceLabel}"]`);
            
            if (currentlyPlaying === audio && !audio.paused) {
                audio.pause();
            } else {
                if (currentlyPlaying && currentlyPlaying !== audio) {
                    const prevAudio = currentlyPlaying;
                    if (!prevAudio.paused) {
                        // Ensure durations are valid before calculation
                        const prevDuration = prevAudio.duration;
                        const targetDuration = audio.duration;
                        
                        if (prevDuration && !isNaN(prevDuration) && targetDuration && !isNaN(targetDuration)) {
                            const currentProgress = prevAudio.currentTime / prevDuration;
                            prevAudio.pause();
                            const repeatSeconds = parseInt(repeatMsInput ? repeatMsInput.value : 250) / 1000;
                            const targetPosition = (currentProgress * targetDuration) - repeatSeconds;
                            audio.currentTime = Math.max(0, targetPosition);
                        } else {
                            prevAudio.pause();
                            audio.currentTime = 0;
                        }
                    }
                }
                
                // Use a promise-based approach to handle play() and potential errors
                const playPromise = audio.play();
                if (playPromise !== undefined) {
                    playPromise.catch(error => {
                        console.error("Playback failed:", error);
                    });
                }
                currentlyPlaying = audio;
            }
            updatePlayState();
        });
    });

    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }

    if (timeSlider) {
        timeSlider.addEventListener('mousedown', () => { isDragging = true; });
        timeSlider.addEventListener('mouseup', () => { isDragging = false; });
        timeSlider.addEventListener('touchstart', () => { isDragging = true; });
        timeSlider.addEventListener('touchend', () => { isDragging = false; });
        timeSlider.addEventListener('input', (e) => {
            if (currentlyPlaying && timeDisplay) {
                const newTime = (e.target.value / 100) * currentlyPlaying.duration;
                const minutes = Math.floor(newTime / 60);
                const seconds = Math.floor(newTime % 60).toString().padStart(2, '0');
                timeDisplay.textContent = `${minutes}:${seconds}`;
            }
        });
        timeSlider.addEventListener('change', (e) => {
            if (currentlyPlaying) {
                currentlyPlaying.currentTime = (e.target.value / 100) * currentlyPlaying.duration;
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && !e.target.matches('input, button, textarea')) {
            e.preventDefault();
            togglePlayPause();
        }
    });

    // --- Table Sorting Logic ---
    const headers = document.querySelectorAll('th[data-sortable]');
    headers.forEach((header) => {
        header.addEventListener('click', () => {
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const currentDir = header.getAttribute('data-sort') === 'asc' ? 'desc' : 'asc';
            const cellIndex = header.cellIndex;
            
            // Reset other headers
            headers.forEach(h => h.setAttribute('data-sort', ''));
            header.setAttribute('data-sort', currentDir);

            rows.sort((rowA, rowB) => {
                const cellA = rowA.querySelectorAll('td')[cellIndex].textContent.trim();
                const cellB = rowB.querySelectorAll('td')[cellIndex].textContent.trim();
                
                // Remove non-numeric characters for comparison if needed
                const valA = cellA.replace(/[^\d.-]/g, '');
                const valB = cellB.replace(/[^\d.-]/g, '');

                if (valA !== '' && valB !== '' && !isNaN(valA) && !isNaN(valB)) {
                    return currentDir === 'asc' ? valA - valB : valB - valA;
                }
                return currentDir === 'asc' ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            });

            rows.forEach((row, i) => {
                const rankCell = row.querySelector('.rank');
                if (rankCell && header.getAttribute('data-column') === 'rating') {
                    rankCell.textContent = i + 1;
                }
                tbody.appendChild(row);
            });
        });
    });

    // --- Column Toggle Logic ---
    const columnToggles = document.querySelectorAll('[data-column-toggle]');
    
    function updateColumnVisibility(columnId, isVisible) {
        const elements = document.querySelectorAll(`[data-column-id="${columnId}"]`);
        elements.forEach(el => {
            if (isVisible) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        });
        // Save to localStorage
        localStorage.setItem(`col-visible-${columnId}`, isVisible);
    }

    columnToggles.forEach(toggle => {
        const columnId = toggle.getAttribute('data-column-toggle');
        
        // Load saved state
        const savedState = localStorage.getItem(`col-visible-${columnId}`);
        if (savedState !== null) {
            const isVisible = savedState === 'true';
            toggle.checked = isVisible;
            updateColumnVisibility(columnId, isVisible);
        }

        toggle.addEventListener('change', (e) => {
            updateColumnVisibility(columnId, e.target.checked);
        });
    });

    const resetBtn = document.getElementById('resetColumnsBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            const defaults = {
                'rating': true,
                'name': true,
                'engine': true,
                'description': true,
                'visual': true,
                'sample': true,
                'confidence': false,
                'range': false,
                'matches': false,
                'record': false,
                'win_rate': false,
                'reliability': false
            };

            columnToggles.forEach(toggle => {
                const columnId = toggle.getAttribute('data-column-toggle');
                const isVisible = !!defaults[columnId];
                toggle.checked = isVisible;
                updateColumnVisibility(columnId, isVisible);
            });
        });
    }
});
