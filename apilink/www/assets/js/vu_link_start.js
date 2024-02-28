// When page is loaded
$(function() {
    gui_update_api_links();
});

$("#link-reload-links").on("click", function() {
    $.get( "/api/v0/link/reload")
      .done(function( e ) {
        location.reload();
      });
});

$("div.vulink-toggle").on("click", function() {
    toggle_link_status(this);
});

$("#modal-upload-image-send").on("click", function() {
    upload_image(this);
});

$("#modal-edit-link-send").on("click", function() {
    update_link(this);
});

$("#modal-add-link-send").on("click", function() {
    add_link(this);
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

async function update_link(element)
{
    let filename = $("#modal-edit-link-filename").val();
    let content = $("#modal-edit-link-content").val();
    let res = false;

    res = await vu_link_post_contents('update', filename, content);

    if (res["status"] === 'ok')
    {
        $('#editLinkModal').modal('hide');
        location.reload();
    }
    else
    {
        console.log("Error saving config file");
        console.log(res);
    }
}

async function add_link(element)
{
    const regex_name = /^[0-9a-z\-\_\ \.]*?$/gim;

    let filename = $("#modal-add-link-name").val();
    let content = $("#modal-add-link-content").val();

    // console.log(filename);
    // console.log(content);

    let valid_name = regex_name.test(filename);

    // Validate name
    if (filename.length < 3)
    {
        $("#modal-add-link-name").addClass("is-invalid");
        console.log("File name too short. Len: "+ filename.length);
        return;
    }
    else if (!valid_name)
    {
        $("#modal-add-link-name").addClass("is-invalid");
        console.log("Invalid file name!");
        return;
    }
    else
    {
        $("#modal-add-link-name").removeClass("is-invalid");
    }

    // Validate content
    if (content.length < 10)
    {
        $("#modal-add-link-content").addClass("is-invalid");
        console.log("Invalid yaml content!. Len: "+ filename.length);
        return;
    }
    else
    {
        $("#modal-add-link-content").removeClass("is-invalid");
    }

    res = await vu_link_post_contents('write', filename, content);

    if (res["status"] === 'ok')
    {
        $('#createLinkModal').modal('hide');
        location.reload();
    }
    else
    {
        console.log("Error creating config file");
        console.log(res);
    }
}

function toggle_link_status(element)
{
    let link_file = $(element).data('vu-link-file');
    let enabled = $(element).data('vu-link-enabled');
    let boolEnabled = (/true/).test(enabled);
    let api_url = '/api/v0/link/enable?link='+ link_file;
    let add_class = 'bg-green';
    let rem_class = 'bg-red';

    // We initialize variables assuming element is disabled
    // Here we switch if element is enabled
    if (boolEnabled)
    {
        api_url = '/api/v0/link/disable?link='+ link_file;
        add_class = 'bg-red';
        rem_class = 'bg-green';
    }

    $.get(api_url)
    .done(function( e ) {
        // Update element
        $(element).addClass(add_class).removeClass(rem_class);
        $(element).data('vu-link-enabled', !boolEnabled);
    });
}


async function gui_update_api_links()
{
    // $("#existing-links").empty();

    const existing_links = await vu_link_get_links();

    if (existing_links.length <= 0)
    {
        $("#empty-card").show();
        return;
    }

    $.each( existing_links, function( key, val )
    {
        let boolEnabled = (/true/).test(val['info']['enabled']);
        let name = val['info']['name'];
        let image = val['info']['image'];
        let file = val['info']['file'];
        let enabled = val['info']['enabled'];
        let description = val['info']['description'];
        let update_period = val['api']['update_period'];
        let ribbon = '';
        let modifiers = "";

        $.each( val['api']['value_modifiers'], function( key, val ) {
            modifiers = modifiers + "- "+ val['fn'] +'<br>';
        });

        if (boolEnabled)
        {
            ribbon = '<div class="ribbon ribbon-top bg-green vulink-toggle" data-bs-toggle="tooltip" data-bs-placement="top" title="Click to Enable/Disable link" data-vu-link-enabled="'+ enabled +'"" data-vu-link-file="'+ file +'"">\
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-plug-connected" width="24" height="24" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 12l5 5l-1.5 1.5a3.536 3.536 0 1 1 -5 -5l1.5 -1.5z" /><path d="M17 12l-5 -5l1.5 -1.5a3.536 3.536 0 1 1 5 5l-1.5 1.5z" /><path d="M3 21l2.5 -2.5" /><path d="M18.5 5.5l2.5 -2.5" /><path d="M10 11l-2 2" /><path d="M13 14l-2 2" /></svg> \
              </div>';
        }
        else
        {

            ribbon = '<div class="ribbon ribbon-top bg-red vulink-toggle" data-bs-toggle="tooltip" data-bs-placement="top" title="Click to Enable/Disable link" data-vu-link-enabled="'+ enabled +'"" data-vu-link-file="'+ file +'"">\
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-plug-connected-x" width="24" height="24" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M20 16l-4 4" /><path d="M7 12l5 5l-1.5 1.5a3.536 3.536 0 1 1 -5 -5l1.5 -1.5z" /><path d="M17 12l-5 -5l1.5 -1.5a3.536 3.536 0 1 1 5 5l-1.5 1.5z" /><path d="M3 21l2.5 -2.5" /><path d="M18.5 5.5l2.5 -2.5" /><path d="M10 11l-2 2" /><path d="M13 14l-2 2" /><path d="M16 16l4 4" /></svg> \
              </div>';
        }


        let edit_button = '\
            <button type="button" class="btn btn-icon">\
            <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-settings-filled" width="24" height="24" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M14.647 4.081a.724 .724 0 0 0 1.08 .448c2.439 -1.485 5.23 1.305 3.745 3.744a.724 .724 0 0 0 .447 1.08c2.775 .673 2.775 4.62 0 5.294a.724 .724 0 0 0 -.448 1.08c1.485 2.439 -1.305 5.23 -3.744 3.745a.724 .724 0 0 0 -1.08 .447c-.673 2.775 -4.62 2.775 -5.294 0a.724 .724 0 0 0 -1.08 -.448c-2.439 1.485 -5.23 -1.305 -3.745 -3.744a.724 .724 0 0 0 -.447 -1.08c-2.775 -.673 -2.775 -4.62 0 -5.294a.724 .724 0 0 0 .448 -1.08c-1.485 -2.439 1.305 -5.23 3.744 -3.745a.722 .722 0 0 0 1.08 -.447c.673 -2.775 4.62 -2.775 5.294 0zm-2.647 4.919a3 3 0 1 0 0 6a3 3 0 0 0 0 -6z" stroke-width="0" fill="currentColor" /></svg>\
            </button>';

        let remove_button = '\
            <button type="button" class="btn btn-icon">\
            <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash-x-filled" width="24" height="24" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M20 6a1 1 0 0 1 .117 1.993l-.117 .007h-.081l-.919 11a3 3 0 0 1 -2.824 2.995l-.176 .005h-8c-1.598 0 -2.904 -1.249 -2.992 -2.75l-.005 -.167l-.923 -11.083h-.08a1 1 0 0 1 -.117 -1.993l.117 -.007h16zm-9.489 5.14a1 1 0 0 0 -1.218 1.567l1.292 1.293l-1.292 1.293l-.083 .094a1 1 0 0 0 1.497 1.32l1.293 -1.292l1.293 1.292l.094 .083a1 1 0 0 0 1.32 -1.497l-1.292 -1.293l1.292 -1.293l.083 -.094a1 1 0 0 0 -1.497 -1.32l-1.293 1.292l-1.293 -1.292l-.094 -.083z" stroke-width="0" fill="currentColor" /><path d="M14 2a2 2 0 0 1 2 2a1 1 0 0 1 -1.993 .117l-.007 -.117h-4l-.007 .117a1 1 0 0 1 -1.993 -.117a2 2 0 0 1 1.85 -1.995l.15 -.005h4z" stroke-width="0" fill="currentColor" /></svg>\
            </button>';



         let element = '\
                <div class="col-3" data-vu-card="'+ file +'">\
                <div class="card ">\
                <div class="img-responsive card-img-top" style="background-image: url(http://localhost:5341/api/v0/image/get?file='+image+')"></div>\
                <div class="card-body">\
                '+ ribbon +' \
                <h3 class="card-title">'+ name +'</h3>\
                <div class="text-secondary card-description">\
                '+ description +'\
                </div>\
                <div class="text-secondary">\
                <div class="row">\
                <div class="col-2 btn btn-icon" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-html="true" title="\
                    <div>File: '+ file +'</div>\
                    <div>Period:'+ update_period + ' seconds</div>\
                    <div>Modifiers:<br>'+ modifiers +'</div>\
                ">\
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-info-circle-filled" width="24" height="24" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 2c5.523 0 10 4.477 10 10a10 10 0 0 1 -19.995 .324l-.005 -.324l.004 -.28c.148 -5.393 4.566 -9.72 9.996 -9.72zm0 9h-1l-.117 .007a1 1 0 0 0 0 1.986l.117 .007v3l.007 .117a1 1 0 0 0 .876 .876l.117 .007h1l.117 -.007a1 1 0 0 0 .876 -.876l.007 -.117l-.007 -.117a1 1 0 0 0 -.764 -.857l-.112 -.02l-.117 -.006v-3l-.007 -.117a1 1 0 0 0 -.876 -.876l-.117 -.007zm.01 -3l-.127 .007a1 1 0 0 0 0 1.986l.117 .007l.127 -.007a1 1 0 0 0 0 -1.986l-.117 -.007z" stroke-width="0" fill="currentColor" /></svg>\
                </div>\
                <div class="col-6"></div>\
                <div class="col-2 text-end vu-link-edit" data-vu-link-file="'+ file +'" data-bs-toggle="modal" data-bs-target="#exampleModal">'+ edit_button +'</div>\
                <div class="col-2 text-end vu-link-delete" data-vu-link-file="'+ file +'">'+ remove_button +'</div>\
                </div>\
                </div>\
                </div>\
                </div>\
                </div>';

       $("#existing-links").append(element);
       $('.card-description').css('height', 105).css('max-height', 105);

    });


    $("div.vulink-toggle").on("click", function(e) {
        e.preventDefault();
        toggle_link_status(this);
    });

    $("div.vu-link-edit").on("click", function(e) {
        editLink(this);
    });

    $("div.vu-link-delete").on("click", function(e) {
        e.preventDefault();
        confirmDelete(this);
    });

    triggerTooltipGen();
}

async function editLink(element)
{
    let link_file = $(element).data('vu-link-file');
    let raw_content = await vu_link_get_link_contents(link_file, true);

    $('#modal-edit-link-filename').val(link_file);
    $('#modal-edit-link-content').val(raw_content);

    console.log(link_file);
    console.log(raw_content);

    // Finally show the modal
    $('#editLinkModal').modal('show');
}


function confirmDelete(element)
{
    let link_file = $(element).data('vu-link-file');

    if (confirm('Are you sure? This can not be undone.')) {
        $.get('/api/v0/link/delete?link='+ link_file)
        .done(function( e ) {
            $('*[data-vu-card="'+ link_file +'"]').remove();
        });
    }
};
