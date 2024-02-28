// When page is loaded
$(function() {
    gui_update_images();
});


$("#modal-upload-image-send").on("click", function() {
    upload_image(this);
});

async function upload_image(element)
{
    const regex_name = /^[0-9a-z\-\_\ ]*?$/gim;

    let filename = $("#modal-upload-image-name").val();
    let file = $("#modal-upload-image-file").prop('files')[0];
    let res = false;

    let valid_name = regex_name.test(filename);

    // Validate name
    if (filename.length < 3)
    {
        $("#modal-upload-image-name").addClass("is-invalid");
        console.log("File name too short. Len: "+ filename.length);
        return;
    }
    else if (!valid_name)
    {
        $("#modal-upload-image-name").addClass("is-invalid");
        console.log("Invalid file name!");
        return;
    }
    else
    {
        $("#modal-upload-image-name").removeClass("is-invalid");
    }

    res = await vu_link_upload_image(filename, file);

    if (res["status"] === 'ok')
    {
        $('#uploadImageModal').modal('hide');
        location.reload();
    }
    else
    {
        console.log("Error uploading images");
        console.log(res);
    }
}

async function gui_update_images()
{
    const existing_images = await vu_link_get_images();
    if (existing_images['images'].length <= 0)
    {
        $("#empty-card").show();
        return;
    }


    $.each( existing_images['images'], function(index, val )
    {
        let boolEnabled = (/true/).test(val['enabled']);
        let name = val;
        let image = val;
        let file = val;

         let element = '\
                <div class="col-2" data-vu-card="'+ file +'">\
                <div class="card ">\
                <div class="img-responsive card-img-top" style="background-image: url(http://localhost:5341/api/v0/image/get?file='+image+')"></div>\
                <div class="card-body">\
                    <div class="ribbon ribbon-top bg-red vulink-img-delete" data-vu-image-file="'+ file +'">\
                        <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash" width="24" height="24" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 7l16 0" /><path d="M10 11l0 6" /><path d="M14 11l0 6" /><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" /></svg>\
                    </div>\
                <h3 class="card-title user-select-all">'+ name +'</h3>\
                </div>\
                </div>\
                </div>';

       $("#existing-links").append(element);
       $('.card-description').css('height', 105).css('max-height', 105);

    });


    $("div.vulink-img-delete").on("click", function(e) {
        e.preventDefault();
        confirmDelete(this);
    });

}


function confirmDelete(element)
{
    let img_file = $(element).data('vu-image-file');

    if (confirm('Are you sure? This can not be undone.')) {
        $.get('/api/v0/image/delete?file='+ img_file)
        .done(function( e ) {
            $('*[data-vu-card="'+ img_file +'"]').remove();
        });
    }
};
