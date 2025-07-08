addEventListener("DOMContentLoaded", function () {
   const role = document.getElementById('id_role')
   const group = document.getElementById('group')
   role.addEventListener('change', function (){

      if (this.value === '2'){
          group.style.display = "block";
      }
      else{
          group.style.display = "none";
      }
   });
});