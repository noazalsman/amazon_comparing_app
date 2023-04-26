const temp_items = {}

document.querySelector('form').addEventListener('submit', (event) => {
    event.preventDefault();
    const searchQuery = document.getElementById('search').value;
    temp_items['searchQuery'] = searchQuery
    performSearch(searchQuery);
});

async function performSearch(query) {
    const response = await fetch(`/search?query=${query}`);

    // for testing:
    // const response = await fetch(`/search`);

    const results = await response.json(); // Assuming the Flask route returns JSON data
    temp_items['results'] = results;

    // Populate the results table with the scraped data
    populateResultsTable(results);
}

function populateResultsTable(results) {
    const resultsTable = document.getElementById("results-table");
    resultsTable.innerHTML = ""; // Clear the table contents

    // // Show the table if there are search results
    // if (results.length > 0) {
    //     document.querySelector('table').style.display = 'table';
    // } else {
    //     document.querySelector('table').style.display = 'none';
    // }

    const item_table = document.getElementById('item-table');
    if(item_table) {
        item_table.remove();
        resultsTable.parentElement.style.display = 'table';
    }

    // Iterate through the results and create table rows
    for (const result of results) {
        const row = document.createElement("tr");

        const nameCell = document.createElement("td");
        nameCell.textContent = result.name;
        row.appendChild(nameCell);

        const imageCell = document.createElement("td");
        const image = document.createElement("img");
        image.src = result.image;
        image.width = 64;
        image.height = 64;
        imageCell.appendChild(image);
        row.appendChild(imageCell);

        resultsTable.appendChild(row);
    }
}


async function fetchProductDetails(asin, itemName, amazon_com_price, itemRating) {
    const response = await fetch('/product-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ asin, amazon_com_price }),
    });
    const prices = await response.json();

    // Create a new table with 6 columns and 2 rows to display the item's name, rating, and prices
    let table = document.createElement('table');
    table.setAttribute('id', 'item-table');
    table.innerHTML = `
        <thead>
            <tr>
                <th>Item Name</th>
                <th>Rating</th>
                <th>Amazon.com</th>
                <th>Amazon.co.uk</th>
                <th>Amazon.de</th>
                <th>Amazon.ca</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>${itemName}</td>
                <td>${itemRating}</td>
                <td>${prices['Amazon.com'] || 'Not found'}</td>
                <td>${prices['Amazon.co.uk'] || 'Not found'}</td>
                <td>${prices['Amazon.de'] || 'Not found'}</td>
                <td>${prices['Amazon.ca'] || 'Not found'}</td>
            </tr>
        </tbody>
    `;

    // Replace the existing results table with the new product details table
    let resultsTable = document.getElementById('results-table');
    let parent = resultsTable.parentElement;
    parent.style.display = 'none';
    parent.parentElement.appendChild(table);
    // parent.parentElement.replaceChild(table, parent);

    const adjustedDate = new Date(new Date().getTime() + 3 * 60 * 60 * 1000);
    const formattedDate = adjustedDate.toISOString().slice(0, 19).replace('T', ' ');

    const dataToSave = {
        query: temp_items['searchQuery'],
        time: formattedDate,
        item_name: itemName,
        amazon_com_price: parseFloat(prices['Amazon.com']),
        amazon_co_uk_price: parseFloat(prices['Amazon.co.uk']),
        amazon_de_price: parseFloat(prices['Amazon.de']),
        amazon_ca_price: parseFloat(prices['Amazon.ca'])
    };

    saveItemData(dataToSave).then(response => {
        alert("item added to database");
    });
}

// Add an event listener to handle clicking on a search result
document.getElementById('results-table').addEventListener('click', (event) => {
    let target = event.target;
    while (target.tagName !== 'TR') {
        target = target.parentElement;
    }
    const asin = temp_items['results'][target.rowIndex - 1]['asin'];
    const itemName = temp_items['results'][target.rowIndex - 1]['name'];
    const amazon_com_price = temp_items['results'][target.rowIndex - 1]['price'];
    const itemRating = temp_items['results'][target.rowIndex - 1]['rating'];
    fetchProductDetails(asin, itemName, amazon_com_price, itemRating);
});


async function saveItemData(data) {
    const response = await fetch('/save-item-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return response.json();
}


