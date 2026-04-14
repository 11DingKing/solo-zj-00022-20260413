// store.js
import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex, axios)

export default new Vuex.Store ({
  state: {
    rowData: [],
    previewData: null,
    previewVisible: false
  },

  actions: {
    loadFiles ({ commit }) {
      axios
           .get('api/files/')
           .then(data => {
             let rowData = data.data
             commit('SET_FILES', rowData)
           })
           .catch(error => {
             console.log(error)
           })
    },

    postFile ({ dispatch, commit }, newFile) {
      const config = {
        onUploadProgress (e) {
          var percentCompleted = Math.round( (e.loaded * 5000) / e.total );
        }
      };
      try {
        axios.post('api/files/', newFile, config,
        { headers: {
          'Content-Type': 'multipart/form-data'
           }
        })
          .then(res => {
            // 上传成功后，重新加载文件列表
            dispatch('loadFiles')
          })
          .catch(error => {
            console.log(error);
          })
      } catch (error) {
        console.log(error);
      }
    },

    deleteFile ({ dispatch }, result_id) {
      axios.delete('api/files/' + result_id)
        .then(res => {
          dispatch('loadFiles')
          console.log(res)
        })
        .catch(error => {
          console.log(error)
      })
    },

    downloadFile ({ dispatch }, filename) {
      axios({
        url: `media/${filename}`,
        method: 'GET',
        responseType: 'blob',
      })
      .then ((res) => {
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
      })
    },

    getPreviewUrl ({ commit, dispatch }, fileId) {
      return axios.get(`api/files/${fileId}/preview-url/`)
        .then(response => {
          commit('SET_PREVIEW_DATA', response.data)
          commit('SET_PREVIEW_VISIBLE', true)
          return response.data
        })
        .catch(error => {
          console.log(error)
          if (error.response && error.response.status === 403) {
            commit('SET_PREVIEW_DATA', {
              file_type: 'forbidden',
              error: error.response.data.message || 'This file type cannot be previewed'
            })
            commit('SET_PREVIEW_VISIBLE', true)
          } else if (error.response && error.response.status === 404) {
            commit('SET_PREVIEW_DATA', {
              file_type: 'other',
              error: 'File not found'
            })
            commit('SET_PREVIEW_VISIBLE', true)
          } else {
            // 其他错误也显示不支持预览的提示
            commit('SET_PREVIEW_DATA', {
              file_type: 'other',
              error: 'Unable to preview this file'
            })
            commit('SET_PREVIEW_VISIBLE', true)
          }
          throw error
        })
    },

    closePreview ({ commit }) {
      commit('SET_PREVIEW_VISIBLE', false)
      commit('SET_PREVIEW_DATA', null)
    }
  },

  mutations: {
    SET_FILES (state, files) {
      state.rowData = files
    },
    POST_FILE (state, newFile) {
      state.rowData.push(newFile)
    },
    SET_PREVIEW_DATA (state, data) {
      state.previewData = data
    },
    SET_PREVIEW_VISIBLE (state, visible) {
      state.previewVisible = visible
    }
  }
})
