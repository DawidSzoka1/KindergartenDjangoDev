document.addEventListener("DOMContentLoaded", function () {
    const days = document.querySelectorAll("#days");
    const dropdown = document.getElementById('wholeDrop');
    days.forEach((elem, count) => {
        elem.addEventListener("click", function (ele) {
            const html = ele.target.innerHTML;

            const day = this.firstChild.innerHTML
            const monthYear = this.parentElement.parentElement.children[0].children[0].innerHTML
            dropdown.style.display = 'block'
            dropdown.children[1].children[0].children[0].children[0].children[0].value = `${day} ${monthYear} 1`
            dropdown.children[1].children[1].children[0].children[0].children[0].value = `${day} ${monthYear} 0`
            dropdown.children[1].children[2].children[0].children[0].children[0].value = `${day} ${monthYear} 2`
            this.appendChild(dropdown)
            console.log('?')
        });
    });
});