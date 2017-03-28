/* jslint browser: true */
var hostname = location.hostname.split('.').slice(1).join('.');
var createDivs = function ( data ) {
	var body = document.querySelector( '.counter');
	var queues = [ 
		[ 'best' ],
		[ 'good', 'decent', 'music' ],
		[ 'pending' ],
		[ 'bad' ],
		['trash' ]
	];

	var prog = document.createElement( 'progress' );
	prog.className = 'progress';
	prog.id = 'progress';
	body.appendChild(prog);


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
	var total = 0 - data.counts.pending - data.counts.total;
	data.counts.good = data.counts.held;
	delete data.counts.held; // deletes property from object

	for ( var queue in data.counts ) {
		if ( data.counts.hasOwnProperty( queue ) ) {
			total += data.counts[queue];
			div = document.getElementById( queue );
			if ( !div ) { continue; }
			var text = data.counts[queue] + ' ' + queue;
			div.innerHTML = '<a href="//' + queue + '.' + hostname + '">' + text + '</a>';
			var size = 0.5 * Math.sqrt(data.counts[queue]) + 'em';
			div.style.height = size;
			div.style.width = size;
			div.style['line-height'] = size;
		}
	}

	var prog = document.getElementById( 'progress' );
	prog.max = data.counts.total;
	prog.value = total;


	div = document.getElementById( 'delta' );
	div.innerHTML = 'Δ' + data.delta + ' ' + Math.round( 100 * total / data.counts.total ) + '%';
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
	getJSON('//api.' + hostname + '/stats.json', function ( e, r ) {
		updateCounts( r );
	} );
}

window.onload = function () {
	getJSON('//api.' + hostname + '/stats.json', function ( e, r ) {
		createDivs( r );
		updateCounts( r );
	} );
};
