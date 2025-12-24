document.addEventListener('DOMContentLoaded', function () {
    const dropdownButton = document.getElementById('dropdownButton');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const dropdownOptions = document.querySelectorAll("#options");
    dropdownOptions.forEach((elem) => {
        elem.addEventListener('change', function (event) {
            dropdownButton.innerText = event.target.value;
        });
    });
});