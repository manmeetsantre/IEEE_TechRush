
        // Theme toggle functionality
        const themeToggle = document.getElementById('theme-toggle');
        const currentTheme = localStorage.getItem('theme');

        // Set initial theme
        if (currentTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        }

        // Toggle theme on button click
        themeToggle.addEventListener('click', () => {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
            localStorage.setItem('theme', isDark ? 'light' : 'dark');
        });

        // Form submission
        document.getElementById('mcqForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const pdfFile = document.getElementById('pdf_file').files[0];
            const questionCount = document.getElementById('question_count').value;
            const difficulty = document.getElementById('difficulty').value;
            const chapter = document.getElementById('chapter').value;

            if (!pdfFile) {
                showError('Please select a PDF file');
                return;
            }

            formData.append('pdf_file', pdfFile);
            formData.append('question_count', questionCount);
            formData.append('difficulty', difficulty);
            formData.append('chapter', chapter);

            // Show loading state
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').textContent = 'Processing...';
            clearMessages();

            try {
                const response = await fetch('/', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    displayResults(data);
                    showSuccess('MCQs generated successfully!');
                } else {
                    showError(data.error || 'An error occurred while generating MCQs');
                }
            } catch (error) {
                showError('Network error: Please check if the backend server is running');
                console.error('Error:', error);
            } finally {
                // Hide loading state
                document.getElementById('loading').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('generateBtn').textContent = 'Generate MCQs';
            }
        });

        function displayResults(data) {
            // Display metadata
            const metadata = data.metadata;
            const timing = data.timing;
            document.getElementById('metadata').innerHTML = `
                <div class="metadata-item">
                    <div class="metadata-label">Chapter(s)</div>
                    <div class="metadata-value">${metadata.chapter}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Difficulty</div>
                    <div class="metadata-value">${metadata.difficulty}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Questions</div>
                    <div class="metadata-value">${metadata.question_count}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Total Time</div>
                    <div class="metadata-value">${timing.total_time}</div>
                </div>
            `;

            // Display summary
            document.getElementById('summaryText').textContent = data.summary;

            // Display MCQs
            document.getElementById('mcqContent').textContent = data.mcqs;

            // Show results
            document.getElementById('results').style.display = 'block';

            // Setup download functionality
            setupDownload(data);
        }

        function setupDownload(data) {
            document.getElementById('downloadBtn').onclick = function() {
                const content = `MCQ Generator Results
        Chapter(s): ${data.metadata.chapter}
        Difficulty: ${data.metadata.difficulty}
        Number of Questions: ${data.metadata.question_count}
        Generated on: ${new Date().toLocaleString()}

        SUMMARY:
        ${data.summary}

        MULTIPLE CHOICE QUESTIONS:
        ${data.mcqs}

        Processing Time: ${data.timing.total_time}
        `;

                const blob = new Blob([content], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `mcq_${data.metadata.chapter}_${new Date().toISOString().split('T')[0]}.txt`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            };
        }

        function showError(message) {
            const errorDiv = document.getElementById('errorMsg');
            errorDiv.innerHTML = `<div class="error">${message}</div>`;
            setTimeout(() => {
                errorDiv.innerHTML = '';
            }, 5000);
        }

        function showSuccess(message) {
            const errorDiv = document.getElementById('errorMsg');
            errorDiv.innerHTML = `<div class="success">${message}</div>`;
            setTimeout(() => {
                errorDiv.innerHTML = '';
            }, 3000);
        }

        function clearMessages() {
            document.getElementById('errorMsg').innerHTML = '';
        }

        // File input styling enhancement
        document.getElementById('pdf_file').addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                const label = document.querySelector('label[for="pdf_file"]');
                label.textContent = `PDF File - ${fileName}`;
                label.style.color = 'var(--header-gradient-start)';
            }
        });