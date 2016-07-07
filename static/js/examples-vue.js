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
    jQuery('template').each(function(){
            var t = jQuery(this);
            var data = {template: '#'+t.attr('id')};
            var props = t.attr('v-props');
            if(props) data['props']=props.split(',');
            Vue.component(t.attr('id'), data);
        });

    self.vue = new Vue({
            el: '#vue',
            data: {
                base: URLS.base,
                responses: {}
            },
            filters: {
                marked: marked
            },
            methods: {
                get: function(url){jQuery.get(url).done(function(data){
                            Vue.set(self.vue.responses, url, data);                            
                        });
                }
            }
        });
    self.onfail = function(data) {
        alert(JSON.stringify(data));
    };
    return self;
};

jQuery(function(){WIDGET = widget();});
