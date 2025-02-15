async function processPdf(apiUrl) {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const pageCount = document.getElementById('pageCount');
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
        preview.innerHTML = `<pre class="mb-0">${data.result.preview}</pre>`;

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