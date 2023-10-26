document.addEventListener('DOMContentLoaded', function () {

    const teachers = document.querySelectorAll("#teacher");
    const search = document.querySelector("[name='search']");
    const button = document.querySelector("#search-button");

    button.addEventListener("click", function () {

        teachers.forEach(elem => {
            if (search.value) {
                if (elem.children[0].children[1].children[0].innerHTML.includes(search.value) == 0) {
                    elem.style.display = 'none';
                }
            }else{
                elem.style.display = 'block';
            }

        });
    });

});