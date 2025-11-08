// RAG System UI - Main JavaScript
class RAGSystem {
    constructor() {

        this.apiBaseUrl = '/api';
        this.documents = [];
        this.queries = [];
        this.isQuerying = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeAnimations();
        this.loadStoredData();
        this.startBackgroundAnimation();
        this.updateStats();
    }

    setupEventListeners() {
        // File upload
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        dropZone.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Query interface
        document.getElementById('query-submit').addEventListener('click', this.handleQuery.bind(this));
        document.getElementById('query-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.handleQuery();
            }
        });

        // Advanced options toggle
        document.getElementById('toggle-advanced').addEventListener('click', this.toggleAdvancedOptions.bind(this));

        // Smooth scrolling for navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    initializeAnimations() {
        // Initialize text splitting for animations
        if (typeof Splitting !== 'undefined') {
            Splitting();
        }

        // Animate hero text
        anime({
            targets: '.splitting-text .char',
            translateY: [100, 0],
            opacity: [0, 1],
            easing: 'easeOutExpo',
            duration: 1000,
            delay: (el, i) => 50 * i
        });

        // Animate stats cards
        anime({
            targets: '.glass-effect',
            translateY: [50, 0],
            opacity: [0, 1],
            easing: 'easeOutExpo',
            duration: 800,
            delay: (el, i) => 200 * i,
            complete: () => {
                this.animateCounters();
            }
        });
    }

    animateCounters() {
        const counters = [
            { element: 'documents-count', target: this.documents.length },
            { element: 'queries-count', target: this.queries.length },
            { element: 'chunks-count', target: this.getTotalChunks() },
            { element: 'tokens-count', target: this.getTotalTokens() }
        ];

        counters.forEach(counter => {
            const element = document.getElementById(counter.element);
            if (element) {
                anime({
                    targets: { count: 0 },
                    count: counter.target,
                    duration: 2000,
                    easing: 'easeOutExpo',
                    update: function(anim) {
                        element.textContent = Math.floor(anim.animatables[0].target.count).toLocaleString();
                    }
                });
            }
        });
    }

    startBackgroundAnimation() {
        // P5.js background animation
        new p5((p) => {
            let particles = [];
            const numParticles = 50;

            p.setup = () => {
                const canvas = p.createCanvas(p.windowWidth, p.windowHeight);
                canvas.parent('p5-background');
                
                for (let i = 0; i < numParticles; i++) {
                    particles.push({
                        x: p.random(p.width),
                        y: p.random(p.height),
                        vx: p.random(-0.5, 0.5),
                        vy: p.random(-0.5, 0.5),
                        size: p.random(2, 6),
                        opacity: p.random(0.1, 0.3)
                    });
                }
            };

            p.draw = () => {
                p.clear();
                
                particles.forEach(particle => {
                    p.fill(20, 184, 166, particle.opacity * 255);
                    p.noStroke();
                    p.circle(particle.x, particle.y, particle.size);
                    
                    particle.x += particle.vx;
                    particle.y += particle.vy;
                    
                    if (particle.x < 0 || particle.x > p.width) particle.vx *= -1;
                    if (particle.y < 0 || particle.y > p.height) particle.vy *= -1;
                });
            };

            p.windowResized = () => {
                p.resizeCanvas(p.windowWidth, p.windowHeight);
            };
        });
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }

    async processFiles(files) {
        const validFiles = files.filter(file => 
            file.type === 'application/pdf' || 
            file.name.endsWith('.txt') ||
            file.type === 'text/plain'
        );

        if (validFiles.length === 0) {
            this.showNotification('Please select PDF or text files only.', 'error');
            return;
        }

        this.showUploadProgress();
        
        const formData = new FormData();
        validFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch(`${this.apiBaseUrl}/ingest`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.handleUploadSuccess(result, validFiles);
        } catch (error) {
            this.showNotification(`Upload failed: ${error.message}`, 'error');
            this.hideUploadProgress();
        }
    }

    showUploadProgress() {
        const progressContainer = document.getElementById('upload-progress');
        progressContainer.classList.remove('hidden');
        
        anime({
            targets: progressContainer,
            opacity: [0, 1],
            translateY: [-20, 0],
            duration: 300,
            easing: 'easeOutQuad'
        });

        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress >= 90) {
                clearInterval(interval);
                return;
            }
            this.updateProgress(progress);
        }, 200);
    }

    updateProgress(percent) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const statusText = document.getElementById('processing-status');
        
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${Math.round(percent)}%`;
        
        if (percent < 30) {
            statusText.textContent = 'Uploading files...';
        } else if (percent < 60) {
            statusText.textContent = 'Processing documents...';
        } else if (percent < 90) {
            statusText.textContent = 'Indexing content...';
        } else {
            statusText.textContent = 'Finalizing...';
        }
    }

    hideUploadProgress() {
        const progressContainer = document.getElementById('upload-progress');
        anime({
            targets: progressContainer,
            opacity: [1, 0],
            translateY: [0, -20],
            duration: 300,
            easing: 'easeInQuad',
            complete: () => {
                progressContainer.classList.add('hidden');
            }
        });
    }

    handleUploadSuccess(result, files) {
        this.updateProgress(100);
        
        setTimeout(() => {
            this.hideUploadProgress();
            this.showNotification(`Successfully processed ${result.inserted_chunks} text chunks from ${files.length} files.`, 'success');
            
            // Add documents to list
            files.forEach(file => {
                if (!this.documents.find(doc => doc.name === file.name)) {
                    this.documents.push({
                        name: file.name,
                        size: file.size,
                        type: file.type,
                        uploadDate: new Date().toISOString(),
                        chunks: Math.floor(result.inserted_chunks / files.length)
                    });
                }
            });
            
            this.updateDocumentsList();
            this.updateStats();
            this.saveStoredData();
        }, 1000);
    }

    updateDocumentsList() {
        const container = document.getElementById('documents-list');
        
        if (this.documents.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-slate-500">
                    <svg class="w-16 h-16 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <p>No documents uploaded yet</p>
                    <p class="text-sm">Upload your first document to get started</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.documents.map(doc => `
            <div class="bg-white rounded-lg shadow p-4 hover-lift">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center">
                            ${this.getFileIcon(doc.type)}
                        </div>
                        <div>
                            <h4 class="font-semibold text-slate-800">${doc.name}</h4>
                            <p class="text-sm text-slate-600">${this.formatFileSize(doc.size)} • ${doc.chunks} chunks</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-sm text-slate-600">${this.formatDate(doc.uploadDate)}</p>
                        <button onclick="ragSystem.deleteDocument('${doc.name}')" class="text-red-500 hover:text-red-700 text-sm">
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Update source filter options
        this.updateSourceFilter();
    }

    getFileIcon(fileType) {
        if (fileType === 'application/pdf') {
            return '<svg class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path></svg>';
        } else {
            return '<svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path></svg>';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }

    updateSourceFilter() {
        const select = document.getElementById('source-filter');
        const currentValue = select.value;
        
        select.innerHTML = '<option value="">All Sources</option>';
        this.documents.forEach(doc => {
            const option = document.createElement('option');
            option.value = doc.name;
            option.textContent = doc.name;
            select.appendChild(option);
        });
        
        select.value = currentValue;
    }

    toggleAdvancedOptions() {
        const options = document.getElementById('advanced-options');
        const arrow = document.getElementById('advanced-arrow');
        
        if (options.classList.contains('hidden')) {
            options.classList.remove('hidden');
            arrow.style.transform = 'rotate(180deg)';
            
            anime({
                targets: options,
                opacity: [0, 1],
                translateY: [-20, 0],
                duration: 300,
                easing: 'easeOutQuad'
            });
        } else {
            anime({
                targets: options,
                opacity: [1, 0],
                translateY: [0, -20],
                duration: 300,
                easing: 'easeInQuad',
                complete: () => {
                    options.classList.add('hidden');
                }
            });
            arrow.style.transform = 'rotate(0deg)';
        }
    }

    async handleQuery() {
        if (this.isQuerying) return;
        
        const queryInput = document.getElementById('query-input');
        const query = queryInput.value.trim();
        
        if (!query) {
            this.showNotification('Please enter a question.', 'error');
            return;
        }

        this.isQuerying = true;
        this.showQueryLoading();

        const queryData = {
            question: query,
            k: parseInt(document.getElementById('results-k').value) || 3,
            score_threshold: parseFloat(document.getElementById('threshold').value) || 0.6,
            filter: {
                source: document.getElementById('source-filter').value || null
            }
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(queryData)
            });

            if (!response.ok) {
                throw new Error(`Query failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.handleQuerySuccess(result, query);
        } catch (error) {
            this.showNotification(`Query failed: ${error.message}`, 'error');
            this.hideQueryLoading();
        }
    }

    showQueryLoading() {
        const button = document.getElementById('query-submit');
        const buttonText = document.getElementById('query-button-text');
        const loading = document.getElementById('query-loading');
        
        button.disabled = true;
        buttonText.textContent = 'Processing...';
        loading.classList.remove('hidden');
    }

    hideQueryLoading() {
        const button = document.getElementById('query-submit');
        const buttonText = document.getElementById('query-button-text');
        const loading = document.getElementById('query-loading');
        
        button.disabled = false;
        buttonText.textContent = 'Ask Question';
        loading.classList.add('hidden');
        this.isQuerying = false;
    }

    handleQuerySuccess(result, query) {
        this.hideQueryLoading();
        
        // Add to query history
        this.queries.unshift({
            question: query,
            answer: result.answer,
            sources: result.sources,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 10 queries
        if (this.queries.length > 10) {
            this.queries = this.queries.slice(0, 10);
        }
        
        this.displayQueryResult(result);
        this.updateQueryHistory();
        this.updateStats();
        this.saveStoredData();
        
        // Clear input
        document.getElementById('query-input').value = '';
    }

    displayQueryResult(result) {
        const resultsContainer = document.getElementById('query-results');
        const sourcesContainer = document.getElementById('query-sources');
        
        // Display answer with typing effect
        resultsContainer.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-start space-x-3">
                    <div class="w-8 h-8 bg-teal-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                        </svg>
                    </div>
                    <div class="flex-1">
                        <div class="bg-slate-50 rounded-lg p-4">
                            <div id="typed-answer" class="text-slate-800 leading-relaxed"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Typewriter effect for answer
        if (typeof Typed !== 'undefined') {
            new Typed('#typed-answer', {
                strings: [result.answer],
                typeSpeed: 30,
                showCursor: false,
                onComplete: () => {
                    this.displaySources(result.sources);
                }
            });
        } else {
            document.getElementById('typed-answer').textContent = result.answer;
            this.displaySources(result.sources);
        }
    }

    displaySources(sources) {
        const sourcesContainer = document.getElementById('query-sources');
        
        if (!sources || sources.length === 0) {
            sourcesContainer.innerHTML = `
                <div class="text-center py-8 text-slate-500">
                    <p>No sources found</p>
                </div>
            `;
            return;
        }
        
        sourcesContainer.innerHTML = sources.map(source => `
            <div class="source-card bg-slate-50 rounded-lg p-4 hover-lift cursor-pointer" onclick="this.classList.toggle('expanded')">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex-1">
                        <h4 class="font-semibold text-slate-800 text-sm truncate">${source.source || 'Unknown Source'}</h4>
                        <p class="text-xs text-slate-600">
                            ${source.page_number ? `Page ${source.page_number} • ` : ''}
                            Similarity: ${Math.round(source.similarity * 100)}%
                        </p>
                    </div>
                    <div class="text-xs text-slate-500">
                        ${source.date_added ? this.formatDate(source.date_added) : ''}
                    </div>
                </div>
                <p class="text-sm text-slate-700 leading-relaxed">${source.snippet}</p>
            </div>
        `).join('');
        
        // Animate sources
        anime({
            targets: '.source-card',
            opacity: [0, 1],
            translateX: [-20, 0],
            duration: 400,
            delay: (el, i) => 100 * i,
            easing: 'easeOutQuad'
        });
    }

    updateQueryHistory() {
        const historyContainer = document.getElementById('query-history');
        
        if (this.queries.length === 0) {
            historyContainer.innerHTML = `
                <div class="text-center py-8 text-slate-500">
                    <p>No queries yet</p>
                </div>
            `;
            return;
        }
        
        historyContainer.innerHTML = this.queries.slice(0, 5).map(query => `
            <div class="bg-slate-50 rounded-lg p-3 cursor-pointer hover:bg-slate-100 transition-colors" onclick="document.getElementById('query-input').value='${query.question.replace(/'/g, "\\'")}'">
                <p class="text-sm font-medium text-slate-800 truncate">${query.question}</p>
                <p class="text-xs text-slate-600">${this.formatDate(query.timestamp)}</p>
            </div>
        `).join('');
    }

    deleteDocument(docName) {
        if (confirm(`Are you sure you want to delete "${docName}"?`)) {
            this.documents = this.documents.filter(doc => doc.name !== docName);
            this.updateDocumentsList();
            this.updateStats();
            this.saveStoredData();
            this.showNotification(`Document "${docName}" deleted.`, 'success');
        }
    }

    updateStats() {
        const stats = {
            documents: this.documents.length,
            queries: this.queries.length,
            chunks: this.getTotalChunks(),
            tokens: this.getTotalTokens()
        };
        
        // Update counter animations
        this.animateCounters();
    }

    getTotalChunks() {
        return this.documents.reduce((total, doc) => total + (doc.chunks || 0), 0);
    }

    getTotalTokens() {
        // Rough estimate: average 100 tokens per chunk
        return this.getTotalChunks() * 100;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform translate-x-full transition-transform duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 4000);
    }

    loadStoredData() {
        try {
            const stored = localStorage.getItem('rag-system-data');
            if (stored) {
                const data = JSON.parse(stored);
                this.documents = data.documents || [];
                this.queries = data.queries || [];
            }
        } catch (error) {
            console.error('Failed to load stored data:', error);
        }
    }

    saveStoredData() {
        try {
            const data = {
                documents: this.documents,
                queries: this.queries
            };
            localStorage.setItem('rag-system-data', JSON.stringify(data));
        } catch (error) {
            console.error('Failed to save data:', error);
        }
    }
}

// Utility functions
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Initialize the RAG System
let ragSystem;
document.addEventListener('DOMContentLoaded', () => {
    ragSystem = new RAGSystem();
});