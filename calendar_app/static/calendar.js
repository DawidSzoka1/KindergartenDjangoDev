document.addEventListener("DOMContentLoaded", function () {
    // 1. Definiujemy funkcję globalnie, aby nowa klasa Calendar (Python) mogła ją wywołać przez onclick
    window.openPresenceModal = function(day) {
        const wholeDrop = document.getElementById('wholeDrop');
        const noSelection = document.getElementById('no-selection-msg');
        const selectedText = document.getElementById('selected-date-text');
        const dayInput = document.getElementById('selected_day_input');
        const currentDayVal = parseInt(document.getElementById('currentDay').value) || 0;

        // Pobieramy aktywną rolę przekazaną z Django do szablonu
        const activeRole = "{{ active_role }}";

        // Logika blokady dat (Rodzic tylko przyszłość, Personel dziś i przyszłość)
        const isTodayOrFuture = day >= currentDayVal;
        const isFutureOnly = day > currentDayVal;

        let canEdit = false;
        if (activeRole === 'parent' && isFutureOnly) {
            canEdit = true;
        } else if ((activeRole === 'director' || activeRole === 'teacher') && isTodayOrFuture) {
            canEdit = true;
        }

        if (canEdit) {
            // UI: Podświetlenie wybranego dnia
            document.querySelectorAll('button[onclick^="openPresenceModal"]').forEach(btn => {
                btn.classList.remove('ring-4', 'ring-primary', 'z-30', 'scale-110');
            });
            const activeBtn = event.currentTarget;
            activeBtn.classList.add('ring-4', 'ring-primary', 'z-30', 'scale-110');

            // Pokazywanie formularza w panelu bocznym
            wholeDrop.style.display = 'block';
            noSelection.style.display = 'none';

            // Ustawianie danych w formularzu
            selectedText.innerText = day + " {{ month_name }}";
            dayInput.value = day;

            // Efekt płynnego przewijania na urządzeniach mobilnych
            if (window.innerWidth < 1024) {
                wholeDrop.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else {
            // Opcjonalnie: poinformuj użytkownika, dlaczego nie może edytować
            alert(activeRole === 'parent' ?
                "Jako rodzic możesz zgłaszać nieobecności tylko z wyprzedzeniem (od jutra)." :
                "Nie można edytować dat historycznych w tym widoku.");
        }
    };
});