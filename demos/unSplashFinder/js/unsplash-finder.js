const pageUrl = url_getbase();
var source; 	//source can be either: image-click (which also is used for url parameters), image-upload, text


window.addEventListener('DOMContentLoaded', (e) => {

	//Event Listeners:
	var imageTiles = document.getElementsByClassName('image-tile');
	for (let i = 0; i < imageTiles.length; i++) {
		imageTiles[i].addEventListener('click', image_click);
	}

	document.getElementById('search-form').addEventListener("submit", function (e) {
		e.preventDefault();
		search_go(document.getElementById('search-text').value, 'text', true);
	});

	document.getElementById('page-logo').addEventListener('click',function(e){
		e.preventDefault();
		image_preview_hide();
		search_text_clear();
		url_clear();
		render_initial();
	});

	image_drop(document.querySelector("#search-text"));
	image_drop(document.querySelector(".image-droppable"));
	

	//Url Parameters:
	var searchQuery = url_get_query();
	if (searchQuery) {
		if (searchQuery.includes('sample_')) {
			search_go(searchQuery, 'image-click');
		}
		else {
			search_go(searchQuery, 'text');
		}
	}
	else {
		render_initial();
	}

	//Tooltips:
	var tooltipElements = document.getElementsByClassName('tooltip');
	for (let i = 0; i < imageTiles.length; i++) {
		tooltipElements[i].addEventListener('mousemove', tooltip_show);
	}
	for (let i = 0; i < imageTiles.length; i++) {
		tooltipElements[i].addEventListener('mouseleave', tooltip_hide);
	}

	//Back button, reload page:
	window.onpopstate = function (e) {
		location.reload();
	}

});

function render_initial() {

	var data = [];

	data[0] = { image: "images/examples/sample_001l2dq7a9prvlx0.jpeg", sampleId: "sample_001l2dq7a9prvlx0", link: "https://unsplash.com/data" }
	data[1] = { image: "images/examples/sample_00abkuq8lh8lklu9.jpeg", sampleId: "sample_00abkuq8lh8lklu9", link: "https://unsplash.com/data" }
	data[2] = { image: "images/examples/sample_00pxa1jxn2znm4qr.jpeg", sampleId: "sample_00pxa1jxn2znm4qr", link: "https://unsplash.com/data" }
	data[3] = { image: "images/examples/sample_00gi43pkyxorg8w0.jpeg", sampleId: "sample_00gi43pkyxorg8w0", link: "https://unsplash.com/data" }
	data[4] = { image: "images/examples/sample_01n8sswvnmjm2prg.jpeg", sampleId: "sample_01n8sswvnmjm2prg", link: "https://unsplash.com/data" }
	data[5] = { image: "images/examples/sample_02qpo6ri960cx64y.jpeg", sampleId: "sample_02qpo6ri960cx64y", link: "https://unsplash.com/data" }
	data[6] = { image: "images/examples/sample_02y8ru5hlk5r854x.jpeg", sampleId: "sample_02y8ru5hlk5r854x", link: "https://unsplash.com/data" }
	data[7] = { image: "images/examples/sample_039vblm24wnks16y.jpeg", sampleId: "sample_039vblm24wnks16y", link: "https://unsplash.com/data" }
	data[8] = { image: "images/examples/sample_0er7x9hep0knhb0e.jpeg", sampleId: "sample_0er7x9hep0knhb0e", link: "https://unsplash.com/data" }
	for (i = 0; i < data.length; i++) {
		render_tile(i, data[i]);
	}

}

function search_go(searchString, source = null, updateUrl = false, sampleId = null) {

	clear_tiles();
	tooltip_hide();
	title_update(searchString, source);
	error_hide();
	
	if (source == "image-click") {
		url_update(sampleId, source, updateUrl);
	}
	else if(source == "image-upload"){
		url_clear();
	}
	else {
		url_update(searchString, source, updateUrl);
	}

	if (window.innerWidth < 700) {
		document.getElementById('results-pane').scrollIntoView();
	}

	if (searchString.includes('sample_')) {
		var data = { sampleId: searchString }
	}
	else {
		var data = { data: searchString }
	}

	const requestOptions = {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	};
	fetch('https://www.nyckel.com/v0.9/functions/3xezcnvymei469pi/search?sampleCount=10&includeData=true', requestOptions)
		.then(response => response.json())
		.then(response => {

			var imageData = response['searchSamples'];
			
			if (source == "image-click") {
				image_preview_show(imageData[0]['data'], source);
				imageData.shift();					//Remove the first result now that we've used it for the preview:
			}
			else if (source == "image-upload"){
				image_preview_show(searchString, source);
			}
			if (source == "text"){
				image_preview_hide();
			}
						
			for (i = 0; i < 9; i++) {
				render_tile(i, {
					image: imageData[i]['data'],
					link: 'https://unsplash.com/data',
					sampleId: imageData[i]['sampleId']
				})
			}

		})
		.catch(function () {

		});

}

function clear_tiles() {
	for (let i = 0; i < 9; i++) {
		document.getElementById('tile-' + String(i)).style.backgroundImage = "none";
	}
}

function render_tile(id, imageData) {
	document.getElementById('tile-image-' + String(id)).style.backgroundImage = "url(" + imageData['image'] + ")";
	document.getElementById('tile-image-' + String(id)).dataset.id = imageData['sampleId'];
	document.getElementById('tile-link-' + String(id)).href = imageData['link'];
}

function image_click(e) {
	e.preventDefault();

	var sampleId = e.srcElement.getAttribute("data-id");
	search_go(sampleId, 'image-click', true, sampleId);
	
}

function title_update(searchString, source) {
	if (source == "text") {
		document.title = "Unsplash Finder - " + searchString;
	}
	else{
		document.title = "Unsplash Finder";
	}
}

function url_getbase() {
	return window.location.href.split('?')[0]
}

function url_update(searchString, source, updateUrl) {
	if (updateUrl) {
		if (searchString) {
			window.history.pushState(Date().toLocaleString(), "Unsplash Finder - " + searchString, pageUrl + "?search=" + searchString);
		}
		else {
			window.history.pushState(Date().toLocaleString(), "Unsplash Finder", pageUrl);
		}
	}
}

function url_clear(){
	window.history.pushState(Date().toLocaleString(), "Unsplash Finder", pageUrl);
}

function url_get_query() {
	const urlParams = new URLSearchParams(window.location.search);
	return urlParams.get('search');
}

function image_upload_click() {

	const file = document.querySelector('input[type=file]').files[0];
	const reader = new FileReader();

	reader.addEventListener("load", function () {
		if (is_file_image(file) == true) {
			search_go(reader.result, 'image-upload');
		}
		else {
			error_show();
		}
	}, false);

	if (file) {
		
		reader.readAsDataURL(file);
	}

}

function image_drop(image_drop_area) {

	var uploaded_image;

	image_drop_area.addEventListener('dragover', (e) => {
		e.stopPropagation();
		e.preventDefault();
		e.dataTransfer.dropEffect = 'copy';
	});

	image_drop_area.addEventListener('drop', (e) => {
		e.stopPropagation();
		e.preventDefault();
		const fileList = event.dataTransfer.files;

		if (is_file_image(fileList[0]) == true) {
			readImage(fileList[0]);
		}
		else {
			error_show();
		}
	});

	readImage = (file) => {
		const reader = new FileReader();
		reader.addEventListener('load', (e) => {
			uploaded_image = e.target.result;
			search_go(uploaded_image, 'image-upload');
		});
		reader.readAsDataURL(file);
	}
}

function image_preview_show(image, source) {
	search_text_clear();
	document.getElementById("ItemPreview").src = image;
	document.querySelector("#current-search-preview").style.display = 'block';
}

function image_preview_hide() {
	document.querySelector("#current-search-preview").style.display = 'none';
}

function search_text_clear(){
	document.querySelector('#search-text').value = "";
}

function error_show() {
	document.querySelector("#current-search-preview").style.display = 'none';
	document.querySelector('.error-message').style.display = 'inline-block';
}

function error_hide() {
	document.querySelector('.error-message').style.display = 'none';
}

function is_file_image(file) {
	const acceptedImageTypes = ['image/gif', 'image/jpeg', 'image/png'];
	return file && acceptedImageTypes.includes(file['type']);
}

function tooltip_show(e) {
	var
		target = this.dataset.tooltiptarget,
		toolTip = document.getElementById(target),
		x = e.clientX,
		y = e.clientY;

	toolTip.style.top = (y + 20) + 'px';
	toolTip.style.left = (x + 20) + 'px';
	toolTip.style.display = 'block';
}

function tooltip_hide() {
	var toolTip = document.querySelector('.tooltip-popup');
	toolTip.style.display = 'none';
}
