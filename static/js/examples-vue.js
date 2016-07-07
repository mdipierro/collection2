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
