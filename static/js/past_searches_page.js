async function fetchPastSearches() {
    try {
        const response = await fetch('/get_past_searches');
        const results = await response.json();
        const tableBody = document.querySelector('table tbody');

        for (const result of results) {
            const row = document.createElement('tr');

            const queryCell = document.createElement('td');
            queryCell.textContent = result.query;
            row.appendChild(queryCell);

            const timeCell = document.createElement('td');
            timeCell.textContent = result.time;
            row.appendChild(timeCell);

            const itemNameCell = document.createElement('td');
            itemNameCell.textContent = result.item_name;
            row.appendChild(itemNameCell);

            const amazonComPriceCell = document.createElement('td');
            amazonComPriceCell.textContent = result.amazon_com_price !== null ? `$${result.amazon_com_price}` : 'Not found';
            row.appendChild(amazonComPriceCell);

            const amazonCoUkPriceCell = document.createElement('td');
            amazonCoUkPriceCell.textContent = result.amazon_co_uk_price !== null ? `$${result.amazon_co_uk_price}` : 'Not found';
            row.appendChild(amazonCoUkPriceCell);

            const amazonDePriceCell = document.createElement('td');
            amazonDePriceCell.textContent = result.amazon_de_price !== null ? `$${result.amazon_de_price}` : 'Not found';
            row.appendChild(amazonDePriceCell);

            const amazonCaPriceCell = document.createElement('td');
            amazonCaPriceCell.textContent = result.amazon_ca_price !== null ? `$${result.amazon_ca_price}` : 'Not found';
            row.appendChild(amazonCaPriceCell);

            tableBody.appendChild(row);
        }
    } catch (error) {
        console.error('Error fetching past searches:', error);
    }
}

// Call the fetchPastSearches function when the page loads
window.addEventListener('DOMContentLoaded', fetchPastSearches);
