(function () {
    const dropzone = document.getElementById('evidencia-dropzone');
    if (!dropzone) return;
    const input = document.getElementById('evidencias-input');
    const idle = document.getElementById('evidencia-idle');
    const preview = document.getElementById('evidencia-preview-grid');
    const MAX_FILES = 10;
    let files = [];

    function sync() {
        const dt = new DataTransfer();
        files.forEach(f => dt.items.add(f));
        input.files = dt.files;
        render();
    }

    function thumbCell(file, index) {
        const cell = document.createElement('div');
        cell.style.cssText = 'position:relative;width:84px;height:84px;border-radius:8px;overflow:hidden;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.05);display:flex;align-items:center;justify-content:center;color:#9ca3af;font-size:.65rem;text-align:center';
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.style.cssText = 'width:100%;height:100%;object-fit:cover';
            img.onload = () => URL.revokeObjectURL(img.src);
            cell.appendChild(img);
        } else if (file.type.startsWith('video/')) {
            cell.textContent = 'vídeo';
        } else if (file.type === 'application/pdf') {
            cell.textContent = 'PDF';
        } else {
            cell.textContent = 'arquivo';
        }
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.setAttribute('aria-label', 'Remover');
        remove.textContent = '×';
        remove.style.cssText = 'position:absolute;top:2px;right:2px;width:18px;height:18px;border-radius:50%;border:0;background:rgba(0,0,0,.65);color:#fff;font-size:.9rem;line-height:1;cursor:pointer';
        remove.addEventListener('click', (ev) => {
            ev.stopPropagation();
            files.splice(index, 1);
            sync();
        });
        cell.appendChild(remove);
        return cell;
    }

    function render() {
        preview.innerHTML = '';
        if (files.length === 0) {
            idle.hidden = false;
            preview.hidden = true;
            return;
        }
        idle.hidden = true;
        preview.hidden = false;
        files.forEach((file, idx) => preview.appendChild(thumbCell(file, idx)));
    }

    function addFiles(list) {
        for (const f of list) {
            if (files.length >= MAX_FILES) break;
            files.push(f);
        }
        sync();
    }

    dropzone.addEventListener('click', (e) => {
        if (e.target.closest('button')) return;
        input.click();
    });
    dropzone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            input.click();
        }
    });
    input.addEventListener('change', () => addFiles(input.files));
    ['dragenter', 'dragover'].forEach(ev => {
        dropzone.addEventListener(ev, (e) => {
            e.preventDefault();
            dropzone.classList.add('is-dragover');
        });
    });
    ['dragleave', 'drop'].forEach(ev => {
        dropzone.addEventListener(ev, (e) => {
            e.preventDefault();
            dropzone.classList.remove('is-dragover');
        });
    });
    dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files);
    });
})();
