import axiosInstance from '@/plugins/axios';


function getBase64(file, callback) {
  const reader = new FileReader();
  reader.addEventListener('load', () => callback(reader.result));
  reader.readAsDataURL(file);
}


const fileUpload = (file, name = 'file', param) => {
  const apiUri = '/photos/file';
  const formData = new FormData();
  formData.append(name, file);
  formData.append('tags', param.tags);
  formData.append('desc', param.desc);
  formData.append('make', param.make);
  formData.append('model', param.model);
  formData.append('width', param.width);
  formData.append('height', param.height);
  formData.append('geotag_lat', param.geotag_lat);
  formData.append('geotag_lng', param.geotag_lng);
  formData.append('taken_date', param.takenDate);
  formData.append('city', param.city);
  formData.append('nation', param.nation);
  formData.append('address', param.address);
  formData.append('filename_orig', param.filename_orig);

  const config = {
    headers: {
      'content-type': 'multipart/form-data',
    },
  };

  console.log('upload');
  console.log(param);
  console.log(axiosInstance.defaults.headers.common.Authorization);

  return axiosInstance.post(apiUri, formData, config);
};


// eslint-disable-next-line
const fileUploadBase64 = (file, name = 'file', param) => {
  const config = {
    headers: {
      'content-type': 'multipart/form-data',
    },
  };

  getBase64(file, (base64Data) => {
    const apiUri = '/photos/file';
    const formData = new FormData();
    // formData.append(name, file, { contentType: 'application/octet-stream' });
    formData.append('tags', param.tags);
    formData.append('desc', param.desc);
    formData.append('make', param.make);
    formData.append('model', param.model);
    formData.append('width', param.width);
    formData.append('height', param.height);
    formData.append('geotag_lat', param.geotag_lat);
    formData.append('geotag_lng', param.geotag_lng);
    formData.append('taken_date', param.takenDate);
    formData.append('city', param.city);
    formData.append('nation', param.nation);
    formData.append('address', param.address);
    formData.append('filename_orig', param.filename_orig);

    console.log(formData.keys());
    // console.log('base 64 of file is', base64Data);
    formData.append('base64_image', base64Data);

    console.log('upload');
    console.log(param);
    console.log(axiosInstance.defaults.headers.common.Authorization);

    return axiosInstance.post(apiUri, formData, config);
  });
};

export default {
  fileUpload,
  fileUploadBase64,
};
