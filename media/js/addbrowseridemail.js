(function($) {
    $().ready(function() {
        bid_selector = '#account .controls .browser_id_add_email';
        var emails = $('#emails').data('emails');

        var write_email = function(emails) {
            $('.user-emails').remove();
            for (var i = 0; i < emails.length; i++) {
                markup = '<div class="user-emails"><span class="delete" data-email="' + emails[i] + '">X</span> <span class="label-text">' +
                         emails[i] + '</span></div>';
                $(markup).insertBefore(bid_selector);
            }
            $('#emails .delete').bind('click', delete_email);
        };

        write_email(emails);

        /* Create BID dialogue for ajax interaction */
        $(bid_selector).bind('click', function(e) {
            e.preventDefault();
            navigator.id.getVerifiedEmail(function(assertion) {
                if (assertion) {
                    $.ajax({
                        type: 'POST',
                        url: '/en-US/user/edit/email',
                        data: {'assertion': assertion},
                        success: function(data){
                            data = JSON.parse(data);
                            if (data['emails']) {
                                write_email(data['emails']);
                            }
                        }
                    });
                }
            });
        });


        var delete_email = function(e) {
            var email = e.target.dataset['email'];
            console.log(email);
            $.ajax({
                type: 'DELETE',
                url: '/en-US/user/edit/email/delete/' + email,
                success: function(data){
                    data = JSON.parse(data);
                    if (data['emails']) {
                        write_email(data['emails']);
                    }
                }
            });
        };
    });
})(jQuery);

jQuery(document).ajaxSend(function(event, xhr, settings) {
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    function getCsrftoken() {
        return $('input[name="csrfmiddlewaretoken"]').attr('value');
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCsrftoken());
    }
});
