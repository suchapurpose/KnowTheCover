const releaseData = release_data;
for (const [key, value] of Object.entries(releaseData)) {
    console.log(`Key: ${key}, Value: ${value}`);
}

function addToCollection() {
    const collectionId = document.getElementById("collection-select").value;
    const release = feteched_release;
    console.log('Adding release to collection:', collectionId, 'and ', release);
    console.log('Release:', release);

    fetch('/add_release_to_collection/', {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}"
        },
        body: JSON.stringify({
            collection_id: collectionId,
            release: release
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Release added to collection successfully!");
        } else {
            alert("Failed to add release to collection!");
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
}
