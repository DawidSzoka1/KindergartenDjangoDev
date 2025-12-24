function myFunction() {
  // Get the checkbox
  const checkBox = document.getElementById("mySwitch");
  // Get the output text

  const end = document.getElementById('end')
  // If the checkbox is checked, display the output text
  if (checkBox.checked == true){
    end.style.display = "none";
  } else {
    end.style.display = "block";
  }
}