function delayedAction(sender, action, interval) {
    if(!interval) {
        interval = 500;
    }
    if(sender.promise_) {
        clearTimeout(sender.promise_);
    }
    sender.promise_ = setTimeout(action, interval);
}

var CACHE = {};
function setupAutoComplete(url, inputId, resultId) {
    $(inputId).autocomplete({
        appendTo: resultId,
        delay: 500,
        minLength: 1,
        source: function(request, response) {
            var q = request.term;
            // TODO
            var qkey = String($('#CorpusSelector').val()) + ': ' + q;
            if (qkey in CACHE) {
                response(CACHE[qkey]);
                return;
            }
            $.ajax({
                url: url,
                dataType: 'json',
                data:{q: q, c: $('#CorpusSelector').val()},
                success: function(r) {
                    var data = $.map(r.gr, function(item){
                        // TODO using template to render
                        var s = item[1];
                        var p1 = s.indexOf('<strong>'), p2 = s.lastIndexOf('</strong>');
                        var begin = Math.max(p1 - Math.floor((74-(p2-p1-25))/2), 0);
                        if(begin > 0 && s[begin] != ' ' && s[begin-1] != ' '){
                            begin += s.slice(begin).indexOf(' ') + 1;
                        }
                        s = s.slice(begin);
                        if(begin > 0)
                            s = '...' + s;
                        var label = '<p class="suggestWord textOverflow">'+ item[0] + '</p>' + '<p class="exampleSentence textOverflow">' + s + '</p>';
                        return {value: item[0], label: label};
                    });
                    CACHE[qkey] = data;
                    response(data);
                },
                fail: function() {
                    response([]);
                }
            });
        },
        html: true
    });
}

/*
 * jQuery UI Autocomplete HTML Extension
 *
 * Copyright 2010, Scott González (http://scottgonzalez.com)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 *
 * http://github.com/scottgonzalez/jquery-ui-extensions
 */
(function( $ ) {

var proto = $.ui.autocomplete.prototype,
    initSource = proto._initSource;

function filter( array, term ) {
    var matcher = new RegExp( $.ui.autocomplete.escapeRegex(term), "i" );
    return $.grep( array, function(value) {
        return matcher.test( $( "<div>" ).html( value.label || value.value || value ).text() );
    });
}

$.extend( proto, {
    _initSource: function() {
        if ( this.options.html && $.isArray(this.options.source) ) {
            this.source = function( request, response ) {
                response( filter( this.options.source, request.term ) );
            };
        } else {
            initSource.call( this );
        }
    },

    _renderItem: function( ul, item) {
        return $( "<li></li>" )
            .data( "item.autocomplete", item )
            .append( $( "<a></a>" )[ this.options.html ? "html" : "text" ]( item.label ) )
            .appendTo( ul );
    }
});

})( jQuery );
