function formatNumber(value) {
  if (value === null || value === undefined) return '';
  
  // Format number with thousands separator and 0 decimals
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
}

function createFinancialTable(tableData) {
  const container = document.createElement('div');
  container.className = 'mb-5';

  // Add table title
  const title = document.createElement('h4');
  title.textContent = tableData.statement;
  container.appendChild(title);

  // Add unit information
  const unit = document.createElement('p');
  unit.className = 'text-muted';
  unit.textContent = `(${tableData.unit})`;
  container.appendChild(unit);

  // Create table
  const table = document.createElement('table');
  table.className = 'table table-bordered table-hover';

  // Create header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  const headers = ['Category', ...Object.keys(tableData.data[0]).filter(key => key !== 'Category')];
  
  headers.forEach(header => {
    const th = document.createElement('th');
    th.textContent = header;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Create body
  const tbody = document.createElement('tbody');
  tableData.data.forEach(row => {
    const tr = document.createElement('tr');
    
    // Add category column
    const tdCategory = document.createElement('td');
    tdCategory.textContent = row.Category;
    tr.appendChild(tdCategory);

    // Add value columns
    headers.slice(1).forEach(year => {
      const td = document.createElement('td');
      const value = row[year];
      td.textContent = formatNumber(value);
      if (value < 0) {
        td.className = 'text-danger';
      }
      td.style.textAlign = 'right';
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  container.appendChild(table);
  return container;
}

async function loadFinanceSectionTables(filename) {
  const tablesContainer = document.getElementById('financial-tables');
  tablesContainer.innerHTML = '<p class="text-muted">Loading financial statements...</p>';

  fetch(`/api/v1/finance_tables/${filename}`)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        tablesContainer.innerHTML = '';
        data.tables.forEach(tableData => {
          const tableElement = createFinancialTable(tableData);
          tablesContainer.appendChild(tableElement);
        });
      } else {
        tablesContainer.innerHTML = '<p class="text-danger">Error loading financial data</p>';
      }
    })
    .catch(error => {
      console.error('Error:', error);
      tablesContainer.innerHTML = '<p class="text-danger">Error loading financial data</p>';
    });
}