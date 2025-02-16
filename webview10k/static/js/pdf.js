function convertMarkdownToHtml(text) {
    // Convert markdown-style bold (**text**) to HTML <strong> tags
    // also remove all remaining * characters
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*/g, '');
}
async function processPdf(apiUrl) {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const pageCount = document.getElementById('pageCount');
    const fiscalYear = document.getElementById('fiscalYear');
    const preview = document.getElementById('preview');

    try {
        // Show loading spinner
        loading.classList.remove('d-none');
        results.classList.add('d-none');

        const response = await fetch(apiUrl, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update the UI with results
        pageCount.textContent = data.result.num_pages;
        fiscalYear.textContent = data.result.fiscal_year_date || '-';
        preview.innerHTML = `<pre class="mb-0">${convertMarkdownToHtml(data.result.preview)}</pre>`;

        // Show results
        results.classList.remove('d-none');
    } catch (error) {
        console.error('Error processing PDF:', error);
        preview.innerHTML = `<div class="alert alert-danger">Error processing PDF: ${error.message}</div>`;
    } finally {
        // Hide loading spinner
        loading.classList.add('d-none');
    }
}
async function loadRiskFactors(filename) {
    const riskFactorsContent = document.getElementById('risk-factors-content');
    try {
        const response = await fetch(`/api/v1/risk_factors/${encodeURIComponent(filename)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Display introduction
        document.getElementById('introduction').innerHTML = `<p>${data.introduction}</p>`;
        
        // Create clickable risk titles
        const titlesHtml = data.risk_titles.map((title, index) => `
            <a href="#" class="list-group-item list-group-item-action" 
               onclick="showRiskDetail(${index})">
                ${title}
            </a>
        `).join('');
        
        document.getElementById('risk-titles').innerHTML = titlesHtml;
        
        // Store data for later use
        window.riskFactorsData = {
            titles: data.risk_titles,
            descriptions: data.risk_descriptions
        };
        
    } catch (error) {
        riskFactorsContent.innerHTML = `<div class="alert alert-danger">Error loading risk factors: ${error.message}</div>`;
    }
}

function showRiskDetail(index) {
    const data = window.riskFactorsData;
    document.getElementById('risk-list-section').style.display = 'none';
    document.getElementById('risk-detail-section').style.display = 'block';
    document.getElementById('risk-detail-title').innerHTML = data.titles[index];
    document.getElementById('risk-detail-description').innerHTML = `<pre class="mb-0">${data.descriptions[index]}</pre>`;
}

function showRiskList() {
    document.getElementById('risk-list-section').style.display = 'block';
    document.getElementById('risk-detail-section').style.display = 'none';
}



async function loadBusinessSection(filename) {
    try {
        const response = await fetch(`/api/v1/section/${encodeURIComponent(filename)}/Item 1`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        document.getElementById('business-text').innerHTML = 
            `<pre>${convertMarkdownToHtml(data.content)}</pre>`;
    } catch (error) {
        document.getElementById('business-text').innerHTML = 
            `<div class="alert alert-danger">Error loading business section: ${error.message}</div>`;
    }
}

async function loadMDASection(filename) {
    try {
        const response = await fetch(`/api/v1/section/${encodeURIComponent(filename)}/Item 7`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        document.getElementById('mda-text').innerHTML = 
            `<pre>${convertMarkdownToHtml(data.content)}</pre>`;
    } catch (error) {
        document.getElementById('mda-text').innerHTML = 
            `<div class="alert alert-danger">Error loading MD&A section: ${error.message}</div>`;
    }
}

async function loadFinanceSection(filename) {
    try {
        const response = await fetch(`/api/v1/section/${encodeURIComponent(filename)}/Item 15`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        document.getElementById('finance-text').innerHTML = 
            `<pre>${convertMarkdownToHtml(data.content)}</pre>`;
    } catch (error) {
        document.getElementById('finance-text').innerHTML = 
            `<div class="alert alert-danger">Error loading financial section: ${error.message}</div>`;
    }
}