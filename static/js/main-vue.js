$.extend({postJSON: function(url, data) {
            var d = {url:url,
                     method:'POST',
                     data:JSON.stringify(data),
                     contentType: 'application/json',
                     processData: false};
            return $.ajax(d);
        }
    });

$.extend({putJSON: function(url, data) {
            var d = {url:url,
                     method:'PUT',
                     data: JSON.stringify(data),
                     contentType: 'application/json',
                     processData: false};
            return $.ajax(d);
        }
    });

var widget = function() {
    self = {};

    Vue.config.delimiters = ['${', '}']
    Vue.config.unsafeDelimiters = ['!{', '}']
    Vue.config.silent = false; // show all warnings
    Vue.config.async = true; // for debugging only
    self.vue = new Vue({
            el: '#vue',
            data: {
                message: 'hello world'
            },
            filters: {
                marked: marked
            },
            methods: {
            }
        });
    self.onfail = function(data) {
        alert(JSON.stringify(data));
    };
};

jQuery(function(){WIDGET = widget();});
