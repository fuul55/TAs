function show(name, anchor_name_open, anchor_name_clos) {
	var elem = document.getElementById(name);
	location.hash = "";
	if (elem.style.display === 'block') {
		elem.style.display = "none";
		location.hash = "#" + anchor_name_clos;
	} else {
	    elem.style.display = "block";
	    location.hash = "#" + anchor_name_open;
	}
}

