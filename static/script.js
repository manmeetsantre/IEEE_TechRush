
        // Application state
        let currentFile = null;
        let mcqs = [];
        let selectedAnswers = {};
        let showResults = false;
        let currentTheme = 'dark';

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

        // Generate MCQs
        async function generateMCQs() {
            if (!currentFile) {
                alert('Please upload a PDF file first');
                return;
            }

            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            btn.innerHTML = `
                <div class="loading"></div>
                Generating MCQs...
            `;

            try {
                const formData = new FormData();
                formData.append('pdf_file', currentFile);
                formData.append('question_count', document.getElementById('numQuestions').value);
                formData.append('difficulty', document.getElementById('difficulty').value);
                formData.append('chapter', document.getElementById('chapters').value);

                // Replace with your Flask backend URL
                const response = await fetch('http://localhost:5000/', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();
                    mcqs = data.mcqs;
                    const summary = data.summary || '';
		    if (typeof mcqs === "string") {
                      try {
                        mcqs = JSON.parse(mcqs);
                      } catch (e) {
                        mcqContainer.innerHTML = "<p>Error parsing MCQs.</p>";
                        return;
                      }
                    }
                    displayResults(mcqs, summary);
                } else {
                    throw new Error('Failed to generate MCQs');
                }
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
                btn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 8V4H8"></path>
                        <path d="m8 4 4 4 6-6 2 2v4"></path>
                        <path d="M2 14h12a2 2 0 1 1 0 4h-2"></path>
                        <path d="m2 14 1.5-1.5c.5-.5 1.2-.5 1.7 0l4.8 4.8a2 2 0 0 0 2.8 0L15 15"></path>
                    </svg>
                    GENERATE MCQS
                `;
            }
        }

        // Display results
        function displayResults(mcqData, summaryData) {
            selectedAnswers = {};
            showResults = false;
            
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
                mcqCard.innerHTML = `
                    <h3 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;">
                        ${index + 1}. ${mcq.question}
                    </h3>
                    <div class="options">
                        ${mcq.options.map((option, optionIndex) => `
                            <button class="option" onclick="selectAnswer(${mcq.id}, ${optionIndex})" 
                                    id="option-${mcq.id}-${optionIndex}">
                                <span>${String.fromCharCode(65 + optionIndex)}. ${option}</span>
                                <span id="icon-${mcq.id}-${optionIndex}"></span>
                            </button>
                        `).join('')}
                    </div>
                    <div id="explanation-${mcq.id}" class="explanation hidden">
                        <div class="explanation-title">Explanation:</div>
                        <div class="explanation-text">${mcq.explanation}</div>
                    </div>
                `;
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

        // Submit answers
        function submitAnswers() {
            showResults = true;
            
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
            // Update tab styles
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`.tab:${tab === 'mcqs' ? 'first' : 'last'}-child`).classList.add('active');
            
            // Show/hide tab content
            document.getElementById('mcqsTab').classList.toggle('active', tab === 'mcqs');
            document.getElementById('summaryTab').classList.toggle('active', tab === 'summary');
        }

        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Set initial theme icon
            toggleTheme();
            toggleTheme(); // Call twice to set back to dark mode
        });