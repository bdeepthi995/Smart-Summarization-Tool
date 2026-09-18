function toggleInputFields() {
    const fileType = document.getElementById('file_type').value;
    document.getElementById('textInput').style.display = fileType === 'text' ? 'block' : 'none';
    document.getElementById('fileUpload').style.display = (fileType === 'document' || fileType === 'excel') ? 'block' : 'none';
    document.getElementById('urlInput').style.display = fileType === 'url' ? 'block' : 'none';
    
    // Reset file inputs when switching types
    if (fileType !== 'document' && fileType !== 'excel') {
        const fileContainer = document.getElementById('fileInputContainer');
        fileContainer.innerHTML = '<input type="file" name="file_input" accept=".txt,.pdf,.docx" multiple>';
    }
}

function addFileInput() {
    const fileContainer = document.getElementById('fileInputContainer');
    const newInput = document.createElement('input');
    newInput.type = 'file';
    newInput.name = 'file_input';
    newInput.accept = ".txt,.pdf,.docx";
    fileContainer.appendChild(newInput);
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("file_type").addEventListener("change", toggleInputFields);
    
    // For download buttons in results page
    let downloadBtn = document.getElementById("download-btn");
    if (downloadBtn) {
        downloadBtn.addEventListener("click", function() {
            let downloadURL = this.getAttribute("data-download");
            if (downloadURL) {
                window.location.href = downloadURL;
            }
        });
    }
});