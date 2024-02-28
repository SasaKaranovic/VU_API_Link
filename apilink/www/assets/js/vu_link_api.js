async function api_request(url)
{
    var items = [];

    await jQuery.ajax({
        url: "/api/v0/" + url,
        success: function (result) {
            if (result['status'] == 'ok')
            {
                $.each( result['data'], function( key, val ) {
                    items[key] = val;
                });
            }
        },
        dataType: 'json'
    });

    return items;
}

async function vu_link_get_images()
{
    let image_list;

    image_list = await api_request('image/list');
    return image_list;
}

async function vu_link_get_links()
{
    let existing_links;

    existing_links = await api_request('link/list');
    return existing_links;
}



async function vu_link_get_link_contents(filename, request_yaml=false)
{
    let content;
    let url = "/api/v0/link/read?link=" + filename

    if (request_yaml)
    {
        url = url + '&type=toml';
    }

    await jQuery.ajax({
        url: url,
        success: function (result) {
            if (result['status'] == 'ok')
            {
                content = result['data']['contents']
            }
        },
        dataType: 'json'
    });


    return content;
}

async function vu_link_post_contents(method, filename, content)
{
    let url = "/api/v0/link/"+ method;
    let res = false;

    res = await jQuery.ajax({
        url: url,
        type: "POST",
        data: { link_filename: filename, link_contents: content },
        success: function (result) {
            // console.log(result);
            if (result['status'] == 'ok')
            {
                return true;
            }
        },
        fail: function(result) {
            // console.log(result);
            return false;
        },
        dataType: 'json'
    });

    return res;
}

async function vu_link_upload_image(filename, file_data)
{
    let url = "/api/v0/image/upload";
    let res = false;

    var form_data = new FormData();
    form_data.append('image_name', filename);
    form_data.append('image_file', file_data);

    res = await jQuery.ajax({
        url: url,
        type: "POST",
        // data: { image_name: filename, image_file: file_data },
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
        success: function (result) {
            // console.log(result);
            if (result['status'] == 'ok')
            {
                return true;
            }
        },
        fail: function(result) {
            // console.log(result);
            return false;
        },
        dataType: 'json'
    });

    return res;
}
