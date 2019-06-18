let socket = io.connect(window.location.href.match(/(.*?)\:/)[1] + '://' + document.domain + ':' + location.port);

let config = {
	bufferSize: 2048
}
let player = new Player(config, socket);

$("#listen").on('click', function() {
	console.log("click on listen");
	if (player.isPlaying()) {
		$(this).find('i').removeClass("fa-volume-up").addClass("fa-volume-mute");
		player.stop();
	}
	else {
		$(this).find('i').removeClass("fa-volume-mute").addClass("fa-volume-up");
		player.play();
	}
});
