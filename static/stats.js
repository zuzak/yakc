/* jslint browser: true */
var createDivs = function ( data ) {
	var body = document.querySelector( '.counter');
	var queues = [ 
		[ 'best' ],
		[ 'held', 'good', 'music' ],
		[ 'pending' ],
		[ 'bad' ],
		['trash' ]
	];

	var delta = document.createElement( 'div' );
	delta.className = 'delta';
	delta.id = 'delta';
	delta.innerHTML = 'Δ0';
	body.appendChild(delta);

	for ( var i = 0; i < queues.length; i++  ) {
		for ( var j = 0; j < queues[i].length; j++ ) {
			var queue = queues[i][j];
			var div = document.createElement( 'div' );
			if ( queue === 'total' ) {
				continue;
			}

			div.className = 'queue ' + queue;
			div.id = queue;
			div.innerHTML = queue;

			body.appendChild( div );

			if ( j < queues[i].length - 1) {
				var sep = document.createElement( 'span' );
				sep.class = 'sep';
				sep.innerHTML = '&#x21c6'; //'&#x2194;';
				body.appendChild( sep );
			}

			if ( queue === 'trash' ) {
				continue;
			}
		}
		var span = document.createElement( 'span' );
		span.className = 'sep';
		if ( i === queue.length ) {
			span.innerHTML = '&#x2193;'; // downwards
		} else if ( i === queue.length - 1) {
			continue;
		} else if ( i === 0 ) {
			span.innerHTML = '&#x2191;'; // upwards
		} else {
			span.innerHTML = '&#x21f5'; //'&#x2195;'; //  updown
		}
		body.appendChild( span );
	}
};
var updateCounts = function ( data ) {
	var div;
	for ( var queue in data.counts ) {
		if ( data.counts.hasOwnProperty( queue ) ) {
			div = document.getElementById( queue );
			if ( !div ) { continue; }
			div.innerHTML = data.counts[queue] + ' ' + queue;
			var size = 0.5 * Math.sqrt(data.counts[queue]) + 'em';
			div.style.height = size;
			div.style.width = size;
			div.style['line-height'] = size;
		}
	}


	div = document.getElementById( 'delta' );
	div.innerHTML = 'Δ' + data.delta;
	if ( data.delta < 0 ) {
		div.className = 'delta negative';
	} else if ( data.delta === 0 ) {
		div.className = 'delta zero';
	} else {
		div.className = 'delta';
	}
	setTimeout(poll, 3000);
};

var getJSON = function(url, callback) {
	// http://stackoverflow.com/a/35970894
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    xhr.onload = function() {
      var status = xhr.status;
      if (status === 200) {
        callback(null, xhr.response);
      } else {
        callback(status);
      }
    };
    xhr.send();
};


function poll() {
	getJSON('//api.webm.website/stats.json', function ( e, r ) {
		updateCounts( r );
	} );
}

window.onload = function () {
	getJSON('//api.webm.website/stats.json', function ( e, r ) {
		createDivs( r );
		updateCounts( r );
	} );
};
