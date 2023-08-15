document.addEventListener("DOMContentLoaded", function () {
    const days = document.querySelectorAll("#days");
    const dropdown = document.getElementById('wholeDrop');
    const currentDay = document.getElementById('currentDay');
    const user = document.getElementById('user');
    days.forEach((elem, count) => {
        elem.addEventListener("click", function (ele) {
            const html = ele.target.innerHTML;

            const day = this.firstChild.innerHTML
            const monthYear = this.parentElement.parentElement.children[0].children[0].innerHTML

            if (user.value === "{'parent.is_parent'}") {
                if (parseInt(day) > parseInt(currentDay.value)) {
                    dropdown.style.display = 'block'
                    console.log(dropdown.children[1].children[0].children[0].children[0].value = `${day} ${monthYear} 2`)
                }
            } else if (parseInt(day) >= currentDay.value) {
                dropdown.style.display = 'block'
                if (user.value === "{'teacher.is_teacher'}") {
                    // do zrobienia
                    console.log(user.value)
                    console.log(dropdown.children[1].children[0].children[0].children[0].value = `${day} ${monthYear} 2`)

                } else {
                    dropdown.children[1].children[0].children[0].children[0].children[0].value = `${day} ${monthYear} 1`;
                    dropdown.children[1].children[1].children[0].children[0].children[0].value = `${day} ${monthYear} 0`;
                    dropdown.children[1].children[2].children[0].children[0].children[0].value = `${day} ${monthYear} 2`;
                }

                this.appendChild(dropdown)
            }

        });
    });
});