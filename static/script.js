
        // Application state
        let currentFile = null;
        let mcqs = [];
        let selectedAnswers = {};
        let showResults = false;
        let currentTheme = 'dark';
        let topicsExtracted = false;
	    let selectedTopics = [];

        const elements = {
            downloadPdf: document.getElementById('downloadPdf'),
            downloadTxt: document.getElementById('downloadTxt'),
            toggleAnswers: document.getElementById('toggleAnswers')
        };

        // Theme toggle
        function toggleTheme() {
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.body.className = `theme-${currentTheme}`;
            
            const icon = document.getElementById('theme-icon');
            if (currentTheme === 'dark') {
                icon.innerHTML = `<circle cx="12" cy="12" r="5"></circle><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"></path>`;
            } else {
                icon.innerHTML = `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>`;
            }
        }

        // File upload handler
        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (file && file.type === 'application/pdf') {
                currentFile = file;
                document.getElementById('fileStatus').innerHTML = `
                    <p style="font-weight: 500; color: #16a34a;">${file.name}</p>
                    <p style="font-size: 0.875rem; opacity: 0.7;">Click to change file</p>
                `;
            } else {
                alert('Please upload a PDF file');
                event.target.value = '';
            }
        }

        function toggleTopic(element, topic) {
            if (element.classList) {
                element.classList.toggle("selected");
                const index = selectedTopics.indexOf(topic);
                if (index === -1) {
                    selectedTopics.push(topic);
                } else {
                    selectedTopics.splice(index, 1);
                }
                document.getElementById('topics').value = selectedTopics.length > 0 ? selectedTopics.join(', ') : 'All';
            } else {
                console.error("Element does not have classList property.");
            }
        }

        // Toggle topic selection
        function toggleTopic(element, topic) {
            element.classList.toggle('selected');
            const index = selectedTopics.indexOf(topic);
            if (index === -1) {
                selectedTopics.push(topic);
            } else {
                selectedTopics.splice(index, 1);
            }
            document.getElementById('topics').value = selectedTopics.length > 0 ? selectedTopics.join(', ') : 'All';
        }

        // Generate MCQs
        async function generateMCQs() {
            if (!currentFile) {
                alert('Please upload a PDF file first');
                return;
            }

            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
	    if (topicsExtracted) {
                btn.innerHTML = `
                    <div class="loading"></div>
                    Generating MCQs...
                `;
	    } else {
		btn.innerHTML = `
                    <div class="loading"></div>
                    Extracting topics...
            `;
	    }

            try {
                const formData = new FormData();
                formData.append('pdf_file', currentFile);
                formData.append('question_count', document.getElementById('numQuestions').value);
                formData.append('difficulty', document.getElementById('difficulty').value);
                formData.append('topic', document.getElementById('topics').value);
                formData.append('provider', document.getElementById('provider').value);
                formData.append('topicsExtracted', topicsExtracted);

                // Replace with your Flask backend URL
                const response = await fetch('http://localhost:5000/' || 'http://127.0.0.1:5000/', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();
                    if (topicsExtracted) {
                    mcqs = data.mcqs;
                    const summary = data.summary || '';

		    if (typeof mcqs === "string") {
            try {
                mcqs = JSON.parse(mcqs);
            } catch (e) {
                console.error("Error parsing MCQs:", e);
                mcqs = [];
            }
            let history = JSON.parse(localStorage.getItem('mcqHistory') || '[]');
        history.push({
            timestamp: new Date().toISOString(),
            topic: document.getElementById('topics').value,
            difficulty: document.getElementById('difficulty').value,
            mcqs: mcqs,
	    summary: summary
        });
        localStorage.setItem('mcqHistory', JSON.stringify(history));
        }
                    displayResults(mcqs, summary);
		    resetTimer();
		    startTimer();
                    topicsExtracted = false;
                } else if (!topicsExtracted) {
                    console.log(data.topics);
                    btn.children[0].outerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-tags-icon lucide-tags">
                        <path d="M13.172 2a2 2 0 0 1 1.414.586l6.71 6.71a2.4 2.4 0 0 1 0 3.408l-4.592 4.592a2.4 2.4 0 0 1-3.408 0l-6.71-6.71A2 2 0 0 1 6 9.172V3a1 1 0 0 1 1-1z"/>
                        <path d="M2 7v6.172a2 2 0 0 0 .586 1.414l6.71 6.71a2.4 2.4 0 0 0 3.191.193"/>
                        <circle cx="10.5" cy="6.5" r=".5" fill="currentColor"/>
                    </svg>
                    `
		    topicDiv = document.querySelector(".topic-badges-container");
		    topicDiv.innerHTML = "";
		    topics = JSON.parse(data.topics);
		  for (let i = 0; i < topics.length; i++) {
        let div = document.createElement("div");
        div.className = "topic-badge-selector";
        div.textContent = topics[i];

        // Pass the current div instead of self
        div.onclick = () => toggleTopic(div, topics[i]);
        
        topicDiv.appendChild(div);
            }
                    topicsExtracted = true;
                }
                else {
                    throw new Error('Failed to generate MCQs');
                }}
            } catch (error) {
                console.error('Error generating MCQs:', error);
                // Mock data for demonstration
                mcqs = [
                    {
                        id: 1,
                        question: "What is the primary function of mitochondria in a cell?",
                        options: [
                            "Protein synthesis",
                            "Energy production",
                            "DNA replication",
                            "Waste removal"
                        ],
                        correctAnswer: 1,
                        explanation: "Mitochondria are known as the powerhouses of the cell because they produce ATP through cellular respiration."
                    },
                    {
                        id: 2,
                        question: "Which programming paradigm does Python primarily support?",
                        options: [
                            "Only object-oriented",
                            "Only functional",
                            "Multi-paradigm",
                            "Only procedural"
                        ],
                        correctAnswer: 2,
                        explanation: "Python supports multiple programming paradigms including object-oriented, functional, and procedural programming."
                    },
                    {
                        id: 3,
                        question: "What is the time complexity of binary search?",
                        options: [
                            "O(n)",
                            "O(log n)",
                            "O(n²)",
                            "O(1)"
                        ],
                        correctAnswer: 1,
                        explanation: "Binary search has O(log n) time complexity because it eliminates half of the remaining elements in each step."
                    }
                ];
                
                const summary = "This document covers fundamental concepts in computer science and biology, including cellular biology, programming paradigms, and algorithm analysis. The content provides a comprehensive overview of these topics with practical examples and theoretical foundations.";
                displayResults(mcqs, summary);
            } finally {
                btn.disabled = false;
		if (topicsExtracted) {
                	btn.innerHTML = `
                    	<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkle-icon lucide-sparkle">
                        <path d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"/>
                    	</svg>
                    	GENERATE MCQS
                	`;
		} else {
			btn.innerHTML = `
                    	<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-tags-icon lucide-tags">
            <path d="M13.172 2a2 2 0 0 1 1.414.586l6.71 6.71a2.4 2.4 0 0 1 0 3.408l-4.592 4.592a2.4 2.4 0 0 1-3.408 0l-6.71-6.71A2 2 0 0 1 6 9.172V3a1 1 0 0 1 1-1z"/>
            <path d="M2 7v6.172a2 2 0 0 0 .586 1.414l6.71 6.71a2.4 2.4 0 0 0 3.191.193"/><circle cx="10.5" cy="6.5" r=".5" fill="currentColor"/>
        </svg>
                    	EXTRACT TOPICS
                	`;
		}
            }
        }

        // Display results
        function displayResults(mcqData, summaryData) {
            selectedAnswers = {};
            showResults = false;
            document.getElementById('my-audio').src = "";
            document.getElementById('resultsSection').classList.remove('hidden');
            document.getElementById('mcqCount').textContent = mcqData.length;
            document.getElementById('summaryText').innerHTML = summaryData;
            
            displayMCQs();
        }

        // Display MCQs
        function displayMCQs() {
            const container = document.getElementById('mcqsList');
            container.innerHTML = '';

            mcqs.forEach((mcq, index) => {
                const mcqCard = document.createElement('div');
                mcqCard.className = 'mcq-card';

                // Header wrapper (topic badge + question)
                const header = document.createElement('div');
                header.className = 'mcq-header'; // flex container for nice layout

                
                // Question
                const questionHeading = document.createElement('h3');
                questionHeading.style.fontSize = '1.125rem';
                questionHeading.style.fontWeight = '600';
                questionHeading.innerHTML = `${index + 1}. ${mcq.question}`;
                
                // append heading to header (so topic + question are on same row)
                header.appendChild(questionHeading);
                
                // Create topic badge
                    const topicDiv = document.createElement('div');
                    topicDiv.className = 'topic-badge';
                    topicDiv.textContent = mcq.topic;
                    header.appendChild(topicDiv);

                // Options
                const optionsContainer = document.createElement('div');
                optionsContainer.className = 'options';
                optionsContainer.innerHTML = mcq.options.map((option, optionIndex) => `
                    <button class="option" onclick="selectAnswer(${mcq.id}, ${optionIndex})" 
                            id="option-${mcq.id}-${optionIndex}">
                        <span>${String.fromCharCode(65 + optionIndex)}. ${option}</span>
                        <span id="icon-${mcq.id}-${optionIndex}"></span>
                    </button>
                `).join('');

                // Explanation
                const explanationDiv = document.createElement('div');
                explanationDiv.id = `explanation-${mcq.id}`;
                explanationDiv.className = 'explanation hidden';
                explanationDiv.innerHTML = `
                    <div class="explanation-title">Explanation:</div>
                    <div class="explanation-text">${mcq.explanation}</div>
                `;

                // Append elements to MCQ card
                mcqCard.appendChild(header);
                mcqCard.appendChild(optionsContainer);
                mcqCard.appendChild(explanationDiv);

                // Append MCQ card to container
                container.appendChild(mcqCard);
            });

            updateSubmitButton();
        }

        
        

        // Select answer
        function selectAnswer(questionId, answerIndex) {
            if (showResults) return;

            selectedAnswers[questionId] = answerIndex;
            updateOptionStyles(questionId, answerIndex);
            updateSubmitButton();
        }

        // Update option styles
        function updateOptionStyles(questionId, selectedIndex) {
            const mcq = mcqs.find(m => m.id === questionId);
            if (!mcq) return;

            mcq.options.forEach((_, optionIndex) => {
                const option = document.getElementById(`option-${questionId}-${optionIndex}`);
                const icon = document.getElementById(`icon-${questionId}-${optionIndex}`);
                
                option.classList.remove('selected', 'correct', 'incorrect');
                icon.innerHTML = '';

                if (showResults) {
                    option.disabled = true;
                    
                    if (optionIndex === mcq.correctAnswer) {
                        option.classList.add('correct');
                        icon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #16a34a;"><path d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="9"></circle></svg>`;
                    } else if (optionIndex === selectedIndex && optionIndex !== mcq.correctAnswer) {
                        option.classList.add('incorrect');
                        icon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #dc2626;"><circle cx="12" cy="12" r="9"></circle><path d="m15 9-6 6"></path><path d="m9 9 6 6"></path></svg>`;
                    }
                } else if (optionIndex === selectedIndex) {
                    option.classList.add('selected');
                }
            });
        }

        // Update submit button
        function updateSubmitButton() {
            const submitSection = document.getElementById('submitSection');
            const allAnswered = Object.keys(selectedAnswers).length === mcqs.length;
            
            if (allAnswered && !showResults) {
                submitSection.classList.remove('hidden');
            } else {
                submitSection.classList.add('hidden');
            }
        }

        function toggleAnswersVisibility() {
            appState.showAnswers = !appState.showAnswers;
            updateAnswersToggleButton();
            updateMCQDisplay();
        }

        // Submit answers
        function submitAnswers() {
            showResults = true;
            stopTimer();
            // Update all option styles
            mcqs.forEach(mcq => {
                updateOptionStyles(mcq.id, selectedAnswers[mcq.id]);
                document.getElementById(`explanation-${mcq.id}`).classList.remove('hidden');
            });

            // Show results card
            const score = calculateScore();
            const percentage = Math.round((score / mcqs.length) * 100);
            
            document.getElementById('scoreText').textContent = 
                `You scored ${score} out of ${mcqs.length} (${percentage}%)`;
            document.getElementById('resultsCard').classList.remove('hidden');
            
            updateSubmitButton();
        }

        // Calculate score
        function calculateScore() {
            let correct = 0;
            mcqs.forEach(mcq => {
                if (selectedAnswers[mcq.id] === mcq.correctAnswer) {
                    correct++;
                }
            });
            return correct;
        }

        function setDownloadLoading(loading) {
            appState.downloadLoading = loading;
            elements.downloadPdf.disabled = loading;
            elements.downloadTxt.disabled = loading;
            
            if (loading) {
                elements.downloadPdf.classList.add('disabled');
                elements.downloadTxt.classList.add('disabled');
            } else {
                elements.downloadPdf.classList.remove('disabled');
                elements.downloadTxt.classList.remove('disabled');
            }
        }

        // Fallback download as text
        function downloadAsText() {
            let content = `MCQ Quiz - ${appState.file?.name || 'Generated Quiz'}\n`;
            content += '='.repeat(50) + '\n\n';
            
            appState.mcqs.forEach((mcq, index) => {
                content += `${index + 1}. ${mcq.question}\n\n`;
                mcq.options.forEach((option, optionIndex) => {
                    const letter = String.fromCharCode(65 + optionIndex);
                    const marker = optionIndex === mcq.correct_answer ? ' (CORRECT)' : '';
                    content += `   ${letter}. ${option}${marker}\n`;
                });
                content += `\n   Explanation: ${mcq.explanation}\n\n`;
                content += '-'.repeat(30) + '\n\n';
            });
            
            const blob = new Blob([content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'MCQ_Quiz.txt';
            a.click();
            window.URL.revokeObjectURL(url);
        }



        // Reset quiz
        function resetQuiz() {
            selectedAnswers = {};
            showResults = false;
            
            document.getElementById('resultsCard').classList.add('hidden');
            
            // Reset all options and hide explanations
            mcqs.forEach(mcq => {
                mcq.options.forEach((_, optionIndex) => {
                    const option = document.getElementById(`option-${mcq.id}-${optionIndex}`);
                    const icon = document.getElementById(`icon-${mcq.id}-${optionIndex}`);
                    
                    option.classList.remove('selected', 'correct', 'incorrect');
                    option.disabled = false;
                    icon.innerHTML = '';
                });
                
                document.getElementById(`explanation-${mcq.id}`).classList.add('hidden');
            });
            
            updateSubmitButton();
        }

        // Switch tabs
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

            if (tab === 'mcqs') {
                document.querySelectorAll('.tab')[0].classList.add('active');
            } else if (tab === 'summary') {
                document.querySelectorAll('.tab')[1].classList.add('active');
            } else if (tab === 'history') {
                document.querySelectorAll('.tab')[2].classList.add('active');
            }

            document.getElementById('mcqsTab').classList.toggle('active', tab === 'mcqs');
            document.getElementById('summaryTab').classList.toggle('active', tab === 'summary');
            document.getElementById('historyTab').classList.toggle('active', tab === 'history');

            if (tab === 'history') {
                loadHistory();
            }
        }



        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Set initial theme icon
            toggleTheme();
            toggleTheme(); // Call twice to set back to dark mode
        });

            function loadHistory() {
                const history = JSON.parse(localStorage.getItem('mcqHistory') || '[]');
                const container = document.getElementById('historyList');
                container.innerHTML = '';

                if (history.length === 0) {
                    container.innerHTML = '<p>No history found.</p>';
                    return;
                }

        history.forEach((entry, index) => {
            const mcqs = entry.mcqs;

            if (Array.isArray(mcqs) && mcqs.length > 0) {
                mcqs.map(mcq => console.log(mcq.question));
            } else {
                console.error('mcqs is not an array or is empty.');
            }

            const entryDiv = document.createElement('div');
            entryDiv.className = 'mcq-card';
            entryDiv.innerHTML = `
                <h3 style="margin-bottom: 0.5rem;">Quiz ${index + 1} - ${entry.difficulty} - ${entry.topic}</h3>
                <small>${new Date(entry.timestamp).toLocaleString()}</small>
                <ul style="margin-top: 0.5rem;">
                    ${Array.isArray(mcqs) && mcqs.length > 0
                        ? mcqs.map(mcq => `<li>${mcq.question}</li>`).join('')
                        : '<li>No questions available</li>'
                    }
                </ul>
            <br>
            <button class="action-btn view-btn" onclick="loadHistoryMCQs(${index})">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye">
                        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    <span>Preview</span>
                </button> 
            `;
            container.appendChild(entryDiv);
        });
            }
        function loadHistoryMCQs(index) {
            const history = JSON.parse(localStorage.getItem('mcqHistory') || '[]');
            if (index >= 0 && index < history.length) {
                mcqs = history[index].mcqs;
		summary = history[index].summary;
                displayResults(mcqs, summary);
                switchTab('mcqs');
            }
        }

        // Preview MCQs
        function previewMCQs() {
            alert("Preview functionality will be implemented here");
            // You can implement a modal or other UI to preview the MCQs
        }

        // Delete MCQs
        function deleteMCQs() {
            if (confirm("Are you sure you want to delete these MCQs?")) {
                mcqs = [];
                document.getElementById('mcqsList').innerHTML = '';
                document.getElementById('resultsSection').classList.add('hidden');
                document.getElementById('mcqCount').textContent = '0';
		        localStorage.setItem('mcqHistory', '')
            }
        }

let startTime;
let updatedTime;
let difference;
let tInterval;
let running = false;

const display = document.getElementById("display");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const resetBtn = document.getElementById("resetBtn");

function startTimer() {
    if (!running) {
        startTime = new Date().getTime() - (difference || 0);
        tInterval = setInterval(updateTime, 1000);
        running = true;
    }
}

function stopTimer() {
    clearInterval(tInterval);
    running = false;
}

function resetTimer() {
    clearInterval(tInterval);
    running = false;
    difference = 0;
    display.innerHTML = "00:00:00";
}

function updateTime() {
    updatedTime = new Date().getTime();
    difference = updatedTime - startTime;

    const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((difference % (1000 * 60)) / 1000);

    display.innerHTML = (hours < 10 ? "0" + hours : hours) + ":" +
                        (minutes < 10 ? "0" + minutes : minutes) + ":" +
                        (seconds < 10 ? "0" + seconds : seconds);
}

startBtn.addEventListener("click", startTimer);
stopBtn.addEventListener("click", stopTimer);
resetBtn.addEventListener("click", resetTimer);
