
// toggle button function-----------------------------------------------------------------------------------------------
function toggleOverlay() {
    var searchOverlay = document.getElementById('search-overlay');

    // Toggle the display property of the overlays
    if (searchOverlay.style.display === 'none') {
        searchOverlay.style.display = 'block';
    } else {
        searchOverlay.style.display = 'none';
    }
}

// Hover function of images-----------------------------------------------------------------------------------------------
function imageHover() {
    const images = document.querySelectorAll('.recording-list');
    const enlargedImageContainer = document.createElement('div');
    enlargedImageContainer.className = 'enlarged-image-container';
    document.body.appendChild(enlargedImageContainer);

    const enlargedImage = document.createElement('img');
    enlargedImage.className = 'enlarged-image';
    enlargedImageContainer.appendChild(enlargedImage);

    images.forEach(img => {
        img.addEventListener('mouseover', function() {
            enlargedImage.src = this.src;
            enlargedImageContainer.style.display = 'block';
            enlargedImageContainer.style.top = '${this.getBoundingClientRect().top}px';
        });

        img.addEventListener('mouseout', function() {
            enlargedImageContainer.style.display = 'none';
        });
    })
}

document.addEventListener('DOMContentLoaded', function() {
    imageHover();
});

// Country Search related functions--------------------------------------------------------------------------------
var overlayDiv = document.getElementById('search-results');

// Global variables to handle pagination
let totalItems = 0;
let allData = []; // Ensure allData is an array
let currentCountryISOA2 = '';

// Function to fetch data
function fetchData(countryISOA2) {
    // Ensure countryISOA2 is not undefined or null
    if (!countryISOA2) {
        console.error("Country ISO A2 is required but not provided.");
        return;
    }
    var selectedReleaseType = getSelectedReleaseType();
    $.ajax({
        url: countrySearchUrl,
        data: { 
            ISO_A2: countryISOA2,
            selected_release_type: selectedReleaseType
        },
        success: function(data) {
            allData = data.releases;
            console.log("releases: ", allData); // Debugging
            fetchCount = data.fetch_count;
            console.log("Fetch Count: ", fetchCount); // Debugging
            updateOverlayContent(countryISOA2, data);
        },
        error: function(error) {
            document.getElementById('search-results').innerHTML = "Error retrieving album cover images from server: " + error;
        }
    });
}

// Function to update the overlay content
function updateOverlayContent(countryISOA2, data) {
    var overlayDiv = document.getElementById('search-results');
    overlayDiv.innerHTML = ''; // Clear existing content

    // Check if allData is defined and is an array
    if (Array.isArray(allData)) {
        for (let i = 0; i < allData.length; i++) {
            let release = allData[i];
            if (release.cover_image && release.cover_image.length > 0) {
                var coverImage = release.cover_image;
                var imgElement = document.createElement("img");
                imgElement.src = coverImage;
                imgElement.title = release.title;
                imgElement.className = "recording-list";
                imgElement.addEventListener('click', function() {
                    addRelease(release);
                });

                // Create a container for the image and button
                var container = document.createElement("div");
                container.className = "recording-list-container";
                container.style.position = "relative";
                container.style.display = "inline-block";

                // Create the button element
                var addToCollectionButton = document.createElement("button");
                addToCollectionButton.innerHTML = "+";
                addToCollectionButton.className = "recording-list-button";
                addToCollectionButton.addEventListener('click', function(event) {
                    event.stopPropagation(); // Prevent the image click event
                    openCollectionOverlay(release);
                });

                overlayDiv.appendChild(imgElement);
                container.appendChild(addToCollectionButton);

                overlayDiv.appendChild(container);
            }
        }
    } else {
        console.log('allData is undefined or not an array');
    }
    updatePaginationControls(countryISOA2, data);
    imageHover();
}

// Function to update pagination controls
function updatePaginationControls(countryISOA2, data) {
    const paginationElement = document.getElementById('pagination-controls');
    paginationElement.innerHTML = ' '; // Clear existing controls

    // Create button for next page
    const nextButton = document.createElement("button");
    nextButton.innerHTML = "Next";
    nextButton.id = "next-btn";
    nextButton.className = "btn btn-custom";
    nextButton.addEventListener('click', function() {
        document.getElementById('search-results').innerHTML = 'Searching for more...';

        fetchData(countryISOA2);
    });
    paginationElement.appendChild(nextButton);
}

// Event handler for country click
function onCountryClick(countryName, countryISOA2) {
    currentCountryISOA2 = countryISOA2;
    document.getElementById('search-name').innerHTML = '<h3>' + 'Searching for cover art in ' + countryName + '</h3>';
    document.getElementById('search-results').innerHTML = '';
    const nextBtn = document.getElementById('next-btn');
    if (nextBtn) {
        nextBtn.style.display = 'none';
    }

    fetchData(currentCountryISOA2);

}

// Map implementation-------------------------------------------------------------------------------------------------------------------
// set initial map
var map = L.map('map').setView([40, 20], 3); 
// Add a resize handler to the map

function resizeMap() {
    // Resize the map to fit the browser window
    map.fitBounds(L.latLngBounds(map.getCenter(), map.getZoom()));
}
// Call the resize function when the map is created or resized
map.on('resize', resizeMap);

var maxBounds = L.latLngBounds(
    L.latLng(-90, -180), // South-West corner
    L.latLng(90, 180)    // North-East corner
);

// Set the maximum bounds on the map
map.setMaxBounds(maxBounds);
map.on('drag', function() {
    map.panInsideBounds(maxBounds, { animate: false });
});

// add OSM tiles
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 10,
    minZoom: 3,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    updateWhenIdle: true,
    keepBuffer: 2
}).addTo(map);

var countryLayer; // to hold the geojson layer

// Function to parse TSV and convert to GeoJSON
function tsvToGeoJSON(tsvData) {
    const rows = d3.tsvParse(tsvData);
    const features = rows.map(row => {
        const geometry = JSON.parse(row.geometry);
        delete row.geometry;
        return {
            type: 'Feature',
            properties: row,
            geometry: geometry
        };
    });
    return {
        type: 'FeatureCollection',
        features: features
    };
}

// Fetch the TSV file and convert it to GeoJSON
fetch(tsvData)
    .then(response => response.arrayBuffer())
    .then(buffer => {
        const decompressed = pako.ungzip(new Uint8Array(buffer), { to: 'string' });
        const geojsonData = tsvToGeoJSON(decompressed);

        // Add the GeoJSON layer to the map
        var countryLayer = L.geoJSON(geojsonData, {
            style: function(feature) {
                return {
                    weight: 1,
                    opacity: 0.5,
                    color: 'transparent'
                };
            },
            onEachFeature: function(feature, layer) {
                layer.on('click', function(e) {
                    countryLayer.resetStyle();
                    layer.setStyle({
                        weight: 1,
                        opacity: 0.5,
                        color: 'orange'
                    });

                    var countryName = feature.properties.NAME;
                    var countryISOA2 = feature.properties.ISO_A2;
                    console.log('Country clicked:', countryName, countryISOA2);
                    onCountryClick(countryName=countryName, countryISOA2=countryISOA2);
                });
            }
        });
        map.addLayer(countryLayer);
    })
    .catch(error => console.error('Error fetching or parsing the TSV file:', error));

// Navbar Search related functions-------------------------------------------------------------------------------------------------------------------------------------

let artistTotalItems = 0;
let artistAllData = [];
let artistCurrentPage = 1;
let artistOffset = 0;

document.getElementById('navbar-search-form').addEventListener('submit', function(event) {
    event.preventDefault();
    artistOffset = 0;
    navbarSearch();
});

function navbarSearch() {
    let searchQuery = document.getElementById('navbar-search-input').value;
    console.log("Search Query:", searchQuery); // Debug log
    if (searchQuery.length != 0) {
        document.getElementById('search-name').innerHTML = '<h3>' + 'Searching for ' + searchQuery + '</h3>';
    }
    document.getElementById('search-results').style.display = 'none';
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    if (prevBtn) {
        prevBtn.style.display = 'none';
    }
    if (nextBtn) {
        nextBtn.style.display = 'none';
    }

    fetchSearchResults(searchQuery, artistCurrentPage, artistOffset);
}

function fetchSearchResults(query, page, offset) {
    selectedReleaseType = getSelectedReleaseType();
    $.ajax({
        url: artistSearchUrl,
        data: { 
            query: query, 
            page: artistCurrentPage, 
            offset: artistOffset,
            selected_release_type: selectedReleaseType
        },
        method: "GET",
        success: function(data) {
            document.getElementById('search-name');
            console.log("Search Results:", data); // Debug log
            artistAllData = data.artist_list;
            artistTotalItems = data.total_items;
            data.current_page = artistCurrentPage;
            displayArtists(data);
        },
        error: function(xhr, status, error) {
            document.getElementById('search-results').innerHTML = '';
        }
    });
}

function displayArtists(data) {
    const artistListContainer = document.getElementById('search-results');
    artistListContainer.innerHTML = ''; // Clear existing content

    if (Array.isArray(data.artist_list) && data.artist_list.length > 0) {
        data.artist_list.forEach(artist => {
            console.log("Artist:", artist); // Debug log
            let overlayDiv = document.createElement('div');
            overlayDiv.textContent = artist.name;

            if (Array.isArray(artist.release_info)) {
                if (artist.release_info.length == 0) {
                    let noCoverText = document.createElement('p');
                    noCoverText.textContent = "No cover images available.";
                    overlayDiv.appendChild(noCoverText);
                }
                else {
                    overlayDiv.appendChild(document.createElement('br')); // Add line break after artist name
                    console.log("Releases:", artist.release_info); // Debug log
                    artist.release_info.forEach(release => {
                        let imgElement = document.createElement('img');
                        imgElement.src = release.cover_image;
                        imgElement.className = "recording-list";
                        imgElement.title = release.title;
                        imgElement.id = release.id;
                        imgElement.addEventListener('click', function() {
                            addRelease(release);
                        });

                        // Create a container for the image and button
                        var container = document.createElement("div");
                        container.className = "recording-list-container";
                        container.style.position = "relative";
                        container.style.display = "inline-block";

                        // Create the button element
                        var addToCollectionButton = document.createElement("button");
                        addToCollectionButton.innerHTML = "+";
                        addToCollectionButton.className = "recording-list-button";
                        addToCollectionButton.addEventListener('click', function(event) {
                            event.stopPropagation(); // Prevent the image click event
                            openCollectionOverlay(release);
                        });
                        overlayDiv.appendChild(imgElement);
                        container.appendChild(addToCollectionButton);
                        overlayDiv.appendChild(container);
                    });
                }
            artistListContainer.appendChild(overlayDiv);
            document.getElementById('search-results').style.display = 'block';
            }
        });
    }

    imageHover();
    updateArtistPaginationControls();
}

function updateArtistPaginationControls() {
    const paginationElement = document.getElementById('pagination-controls');
    paginationElement.innerHTML = ' '; // Clear existing controls

    // Create button for previous page
    const prevButton = document.createElement("button");
    prevButton.innerHTML = "Previous";
    prevButton.id = "prev-btn";
    prevButton.className = "btn btn-custom prev-btn";
    // Disable Previous Button if on the first page
    prevButton.disabled = artistCurrentPage <= 1;

    prevButton.addEventListener('click', function() {
        artistCurrentPage--;
        artistOffset -= 2;
        console.log("Current Page:", artistCurrentPage, "Offset:", artistOffset); // Debug log
        fetchSearchResults(document.getElementById('navbar-search-input').value, artistCurrentPage, artistOffset);
    });
    paginationElement.appendChild(prevButton);

    // Create button for next page
    const nextButton = document.createElement("button");
    nextButton.innerHTML = "Next";
    nextButton.id = "next-btn";
    nextButton.className = "btn btn-custom";

    // Disable Next Button if there are no more artists
    nextButton.disabled = (artistCurrentPage * 2) >= artistTotalItems;

    nextButton.addEventListener('click', function() {
        document.getElementById('search-results').innerHTML = 'Searching for more...';
        artistCurrentPage++;
        artistOffset += 2;
        console.log("Current Page:", artistCurrentPage, "Offset:", artistOffset); // Debug log
        fetchSearchResults(document.getElementById('navbar-search-input').value, artistCurrentPage, artistOffset);
    });
    paginationElement.appendChild(nextButton);
}

// Click function of images-----------------------------------------------------------------------------------------------

// 
function openCollectionOverlay(release) {
    fetch('/collections/get_user_collections/')
        .then(response => response.json())
        .then(data => {
            const collectionOverlay = document.getElementById('collection-overlay');
            const collectionList = document.getElementById('collection-list');
            collectionList.innerHTML = '';

            data.collections.forEach(collection => {
                const listItem = document.createElement('li');
                listItem.textContent = collection.name;
                listItem.dataset.collectionId = collection.id;
                listItem.classList.add('list-group-item'); // Add Bootstrap class
                console.log("Collection id:", collection.id);
                console.log('Collection:', collection);
                listItem.addEventListener('click', () => {
                    addReleaseToCollection(collection.id, release);
                });
                collectionList.appendChild(listItem);
            });
            document.getElementById('overlay-background').style.display = 'block';
            collectionOverlay.style.display = 'block';
        })
        .catch(error => {
            console.error('Error fetching collections:', error);
        });
}

function addRelease(release) {
    console.log('Adding release:', release);
    console.log('Release:', release);

    const endpoint = `/release/${release.id}/`;

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // CSRF token handling
        },
        body: JSON.stringify({
            release: release
        })
    })
    .then(response => {
        if (!response.ok) {
            // Handle non-JSON response
            return response.text().then(text => {
                throw new Error(`Server error: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Response:', data);
        if (data.success) {
            // Open the release detail page in a new tab
            window.open(`/release/${release.id}/`, '_blank');
        } else {
            alert('Failed to add release: ' + data.error);
        }
    })
    .catch(error => {
        window.open(`/release/${release.id}/`, '_blank');
        console.error('Error:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
    });
}

function addReleaseToCollection(collectionId, release) {
    console.log('Adding release to collection:', collectionId, release);
    console.log('Release:', release);

    fetch('/add_release_to_collection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // CSRF token handling
        },
        body: JSON.stringify({
            collection_id: collectionId,
            release: release
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Release added to collection successfully!');
            document.getElementById('collection-overlay').style.display = 'none';
            document.getElementById('overlay-background').style.display = 'block';
        } else {
            alert('Failed to add release to collection: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error adding release to collection:', error);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to close the collection overlay
function closeCollectionOverlay() {
    document.getElementById('overlay-background').style.display = 'none';
    var collectionOverlay = document.getElementById('collection-overlay');
    collectionOverlay.style.display = 'none';
}

// Add click event listeners to search-overlay images
document.querySelectorAll('.recording-list').forEach(img => {
    img.addEventListener('click', function() {
        openCollectionOverlay(this.src);
    });
});

// Add click event listener to the overlay background to close the collection overlay
document.getElementById('overlay-background').addEventListener('click', closeCollectionOverlay);

// Add click event listeners to search-overlay images
document.querySelectorAll('.recording-list').forEach(img => {
    img.addEventListener('click', function() {
        openCollectionOverlay(this.src);
    });
});
// Filters-------------------------------------------------------------------------------------------------------------------
document.getElementById('show-checkboxes-btn').addEventListener('click', function() {
    var checkboxesContainer = document.getElementById('checkboxes-container');
    if (checkboxesContainer.style.display === 'none' || checkboxesContainer.style.display === '') {
        checkboxesContainer.style.display = 'block';
    } else {
        checkboxesContainer.style.display = 'none';
    }
});

document.querySelectorAll('input[name="release_type"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        if (this.checked) {
            document.querySelectorAll('input[name="release_type"]').forEach(otherCheckbox => {
                if (otherCheckbox !== this) {
                    otherCheckbox.checked = false;
                }
            });
        }
    });
});

function getSelectedReleaseType() {
    var checkbox = document.querySelector('input[name="release_type"]:checked');
    var selectedReleaseType = checkbox ? checkbox.value : '';
    return selectedReleaseType;
}