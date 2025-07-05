const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('fileElem');
const uploadedImages = document.getElementById('uploaded-images');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, e => e.preventDefault(), false);
    dropArea.addEventListener(eventName, e => e.stopPropagation(), false);
});

dropArea.addEventListener('dragover', () => dropArea.classList.add('dragover'));
dropArea.addEventListener('dragleave', () => dropArea.classList.remove('dragover'));
dropArea.addEventListener('drop', handleDrop);
fileInput.addEventListener('change', handleFiles);

function handleDrop(e) {
    dropArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleUpload(files);
}

function handleFiles(e) {
    const files = e.target.files;
    handleUpload(files);
}

async function handleUpload(files) {
    uploadedImages.innerHTML = '<label for="upload-url">Current Upload</label>';

    const uploadPromises = [...files].map(async (file) => {
        if (file.size > 5 * 1024 * 1024) {
            alert(`File "${file.name}" exceeds 5MB limit.`);
            return null;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                // пытаемся считать JSON с ошибкой
                let errorData;
                try {
                    errorData = await res.json();
                } catch {
                    throw new Error(`Upload failed for ${file.name} with status ${res.status}`);
                }
                throw new Error(errorData.detail || `Upload failed for ${file.name}`);
            }

            const data = await res.json();

            const uploadedItem = document.createElement('div');
            const server_name = window.location.host;
            uploadedItem.className = 'preview';
            uploadedItem.innerHTML = `
<input type="text" value="http://${server_name}${data.url}" readonly />
<button onclick="copyToClipboard(this)">COPY</button>
`;

            const link = document.createElement('a');
            link.setAttribute('href', data.url);
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            link.appendChild(img);
            uploadedItem.appendChild(link);

            uploadedImages.appendChild(uploadedItem);

            return data.url;

        } catch (err) {
            alert(err.message);
            return null;
        }
    });

    // Чтобы дождаться все загрузки (если нужно)
    await Promise.all(uploadPromises);
}



function copyToClipboard(button) {
    // Находим ближайший родитель .preview
    const preview = button.closest('.preview');
    if (!preview) return;

    // Внутри preview ищем input[type="text"]
    const input = preview.querySelector('input[type="text"]');
    if (!input) return;
    input.select();

    document.execCommand('copy');
    alert('Copied to clipboard!');
}