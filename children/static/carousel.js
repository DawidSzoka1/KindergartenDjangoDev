addEventListener('DOMContentLoaded', function () {
    let items = document.querySelectorAll('.carousel .carousel-item')
    const amount = document.getElementById('amount')

    items.forEach((el) => {
        let minPerSlide = parseInt(amount.value)
        if (parseInt(amount.value) <= 4) {
            minPerSlide = 4
        }

        let next = el.nextElementSibling
        for (let i = 1; i < minPerSlide; i++) {
            if (!next) {
                // wrap carousel by using first child
                next = items[0]
            }
            let cloneChild = next.cloneNode(true)
            el.appendChild(cloneChild.children[0])
            next = next.nextElementSibling
        }
    })
})
