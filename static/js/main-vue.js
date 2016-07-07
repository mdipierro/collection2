$.extend({postJSON: function(url, data, not_async) {
            var d = {url:url,
                     method:'POST',
                     contentType: 'application/json',
                     processData: false};
            if(data) d.data = JSON.stringify(data);
            if(not_async) d.async = false;
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
