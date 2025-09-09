/**
 * AI-HR Admin Panel JavaScript
 * Handles API interactions for CV management, search, and report generation
 */

// API Configuration
const API_CONFIG = {
    CV_SERVICE: 'http://localhost:8007',
    REPORT_SERVICE: 'http://localhost:8005',
    MAIN_API: 'http://localhost:8006'
};

// Utility functions
function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 5000);
}

function showLoading(elementId, message = 'Загрузка...') {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            ${message}
        </div>
    `;
}

function hideElement(elementId) {
    document.getElementById(elementId).classList.add('hidden');
}

function showElement(elementId) {
    document.getElementById(elementId).classList.remove('hidden');
}

// API functions
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// CV Management functions
async function loadCVList() {
    showLoading('cv-list', 'Загрузка списка резюме...');
    
    try {
        const data = await apiRequest(`${API_CONFIG.CV_SERVICE}/cvs/list`);
        
        if (data.cv_ids && data.cv_ids.length > 0) {
            const cvListHtml = data.cv_ids.map(cvId => `
                <div class="cv-item">
                    <span class="cv-id">${cvId}</span>
                    <button class="btn btn-danger" onclick="deleteCV('${cvId}')" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">Удалить</button>
                </div>
            `).join('');
            
            document.getElementById('cv-list').innerHTML = cvListHtml;
            showStatus(`Загружено ${data.total} резюме`, 'success');
        } else {
            document.getElementById('cv-list').innerHTML = '<div class="loading">Резюме не найдены</div>';
            showStatus('Резюме не найдены', 'info');
        }
    } catch (error) {
        document.getElementById('cv-list').innerHTML = '<div class="loading">Ошибка загрузки</div>';
        showStatus(`Ошибка загрузки списка: ${error.message}`, 'error');
    }
}

async function deleteCV(cvId) {
    if (!confirm(`Удалить резюме ${cvId}?`)) {
        return;
    }
    
    try {
        await apiRequest(`${API_CONFIG.CV_SERVICE}/cvs/${cvId}`, {
            method: 'DELETE'
        });
        
        showStatus(`Резюме ${cvId} удалено`, 'success');
        loadCVList(); // Refresh the list
    } catch (error) {
        showStatus(`Ошибка удаления: ${error.message}`, 'error');
    }
}

// Search functions
async function searchCVs() {
    const query = document.getElementById('search-query').value.trim();
    const limit = document.getElementById('search-limit').value;
    
    if (!query) {
        showStatus('Введите поисковый запрос', 'error');
        return;
    }
    
    showLoading('search-results', 'Поиск по резюме...');
    showElement('search-results');
    
    try {
        const data = await apiRequest(`${API_CONFIG.CV_SERVICE}/cvs/search?q=${encodeURIComponent(query)}&top_k=${limit}`);
        
        if (data.results && data.results.length > 0) {
            const resultsHtml = data.results.map(result => `
                <div class="search-result">
                    <h4>${result.filename} (${result.cv_id})</h4>
                    <span class="score">Релевантность: ${(result.score * 100).toFixed(1)}%</span>
                    <div class="text">${result.chunk_text}</div>
                </div>
            `).join('');
            
            document.getElementById('search-results').innerHTML = resultsHtml;
            showStatus(`Найдено ${data.total} результатов для "${query}"`, 'success');
        } else {
            document.getElementById('search-results').innerHTML = '<div class="loading">Результаты не найдены</div>';
            showStatus(`Результаты не найдены для "${query}"`, 'info');
        }
    } catch (error) {
        document.getElementById('search-results').innerHTML = '<div class="loading">Ошибка поиска</div>';
        showStatus(`Ошибка поиска: ${error.message}`, 'error');
    }
}

// Report generation functions
async function generateReport() {
    const candidate = document.getElementById('report-candidate').value.trim();
    const position = document.getElementById('report-position').value.trim();
    const experience = document.getElementById('report-experience').value.trim();
    const rating = parseFloat(document.getElementById('report-rating').value);
    const positives = document.getElementById('report-positives').value.trim();
    const negatives = document.getElementById('report-negatives').value.trim();
    
    if (!candidate || !position) {
        showStatus('Заполните обязательные поля: имя кандидата и позиция', 'error');
        return;
    }
    
    if (isNaN(rating) || rating < 0 || rating > 10) {
        showStatus('Оценка должна быть числом от 0 до 10', 'error');
        return;
    }
    
    const reportData = {
        candidate: {
            name: candidate,
            experience: experience,
            location: 'Москва'
        },
        vacancy: {
            title: position,
            department: 'IT',
            level: 'Senior'
        },
        blocks: [
            { name: 'Python', score: 0.8, weight: 0.4 },
            { name: 'Django', score: 0.7, weight: 0.35 },
            { name: 'Database', score: 0.6, weight: 0.25 }
        ],
        positives: positives ? positives.split(',').map(s => s.trim()).filter(s => s) : [],
        negatives: negatives ? negatives.split(',').map(s => s.trim()).filter(s => s) : [],
        quotes: [
            {
                text: `Кандидат ${candidate} имеет опыт работы с ${position}`,
                source: 'Interview Summary'
            }
        ],
        rating_0_10: rating
    };
    
    try {
        showStatus('Генерация отчёта...', 'info');
        
        const response = await fetch(`${API_CONFIG.REPORT_SERVICE}/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reportData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Get the PDF blob
        const pdfBlob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(pdfBlob);
        const downloadLink = document.getElementById('download-link');
        downloadLink.href = url;
        downloadLink.download = `interview_report_${candidate.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
        downloadLink.classList.remove('hidden');
        
        showStatus('Отчёт успешно сгенерирован!', 'success');
        
    } catch (error) {
        showStatus(`Ошибка генерации отчёта: ${error.message}`, 'error');
    }
}

// Service status functions
async function checkServices() {
    showLoading('services-status', 'Проверка статуса сервисов...');
    
    const services = [
        { name: 'CV Service', url: `${API_CONFIG.CV_SERVICE}/health` },
        { name: 'Report Service', url: `${API_CONFIG.REPORT_SERVICE}/health` },
        { name: 'Main API', url: `${API_CONFIG.MAIN_API}/health` }
    ];
    
    const statusChecks = await Promise.allSettled(
        services.map(async (service) => {
            try {
                const data = await apiRequest(service.url);
                return { ...service, status: 'ok', data };
            } catch (error) {
                return { ...service, status: 'error', error: error.message };
            }
        })
    );
    
    const statusHtml = statusChecks.map((result, index) => {
        const service = services[index];
        const check = result.status === 'fulfilled' ? result.value : { ...service, status: 'error', error: result.reason };
        
        const statusClass = check.status === 'ok' ? 'success' : 'error';
        const statusText = check.status === 'ok' ? '✅ Работает' : '❌ Ошибка';
        
        return `
            <div class="cv-item">
                <span><strong>${service.name}</strong></span>
                <span class="status ${statusClass}">${statusText}</span>
            </div>
        `;
    }).join('');
    
    document.getElementById('services-status').innerHTML = statusHtml;
    showStatus('Проверка сервисов завершена', 'success');
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load CV list on page load
    loadCVList();
    
    // Check services on page load
    checkServices();
    
    // Add Enter key support for search
    document.getElementById('search-query').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchCVs();
        }
    });
    
    // Add Enter key support for report generation
    document.getElementById('report-candidate').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            generateReport();
        }
    });
    
    document.getElementById('report-position').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            generateReport();
        }
    });
});

// Global functions for HTML onclick handlers
window.loadCVList = loadCVList;
window.searchCVs = searchCVs;
window.generateReport = generateReport;
window.checkServices = checkServices;
window.deleteCV = deleteCV;
