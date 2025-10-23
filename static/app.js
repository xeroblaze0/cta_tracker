document.addEventListener('DOMContentLoaded', function () {
    fetch('/map')
        .then(response => response.text())
        .then(data => {
            const mapElement = document.getElementById('map');
            mapElement.innerHTML = data;
            const scripts = mapElement.getElementsByTagName('script');
            for (let i = 0; i < scripts.length; i++) {
                const script = document.createElement('script');
                script.type = scripts[i].type || 'text/javascript';
                if (scripts[i].src) {
                    script.src = scripts[i].src;
                } else {
                    script.text = scripts[i].innerText;
                }
                document.head.appendChild(script);
            }
        });
});
