package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

func create_folder(folder string) error {
	if _, err := os.Stat(folder); errors.Is(err, os.ErrNotExist) {
		// in this case the folder does not exist
		log.Println("Creating folder:", folder)
		err := os.Mkdir(folder, 0755)
		if err != nil {
			log.Fatal("Cannot create folder:", err)
			return err
		}
	}
	return nil
}

/*
This function takes in a filepath, reads it line by line, loads the json data
and then returns a list of these json objects
*/
func get_data(filepath string) ([]interface{}, map[string]interface{}) {
	filepath_split := strings.Split(filepath, "/")
	folder_path := strings.Join(filepath_split[:len(filepath_split)-1], "/")
	_ = create_folder(folder_path)

	if _, err := os.Stat(filepath); err == nil {
		// in this case the file exists
		f, err := os.OpenFile(filepath, os.O_RDONLY, 0600)
		if err != nil {
			log.Fatal("Cannot open file: ", err)
		}
		defer f.Close()

		// filepath is a .jsonl file so load all the records and return the data
		// read all the data
		data, err := ioutil.ReadAll(f)
		if err != nil {
			log.Fatal("Cannot read the file: ", err)
		}

		// now split the data by newline
		data_split := strings.Split(string(data), "\n")
		// remove the last empty string
		data_split = data_split[:len(data_split)-1]

		// now loop through the data and unmarshal each line
		all_data := make([]interface{}, 0)
		job_wise_dict := make(map[string]interface{})
		for _, line := range data_split {
			// going over each line and adding to the 1D list
			var jsonData map[string]interface{}
			json.Unmarshal([]byte(line), &jsonData)
			all_data = append(all_data, jsonData)

			// and then to the job wise dict
			job_id := jsonData["job_id"].(string)
			if _, ok := job_wise_dict[job_id]; !ok {
				job_wise_dict[job_id] = []interface{}{jsonData}
			} else {
				// append the data to the existing value
				job_wise_dict[job_id] = append(job_wise_dict[job_id].([]interface{}), jsonData)
			}
		}
		fmt.Println("======== Data Statistics ========")
		fmt.Println(">>> Data Loaded from file:", filepath)
		fmt.Println(">>>         Total samples:", len(all_data))
		fmt.Println(">>>         Total jobs:", len(job_wise_dict))
		fmt.Println("=================================")
		return all_data, job_wise_dict

	} else if errors.Is(err, os.ErrNotExist) {
		// this is the error you get when the file does not exist -> create a new file then
		log.Println("creating file " + filepath)
		_, err := os.Create(filepath)
		if err != nil {
			log.Fatal("Cannot create a new file:" + err.Error())
		}
	} else {
		// Schrodinger: file may or may not exist. See err for details.
		log.Fatal("Something went wrong:" + err.Error())
	}

	return nil, nil
}

func cleanup(data []interface{}, filepath string) {
	// save the data at filepath (overwrite)
	f, err := os.OpenFile(filepath, os.O_WRONLY|os.O_TRUNC, 0600)
	if err != nil {
		log.Fatal("Cannot open file: ", err)
	}
	defer f.Close()

	string_to_write := ""
	for _, line := range data {
		json_line, err := json.Marshal(line)
		if err != nil {
			log.Fatal("Cannot marshal data: ", err)
		}
		string_to_write += string(json_line) + "\n"
	}
	_, err = f.WriteString(string_to_write)
	if err != nil {
		log.Fatal("Cannot write to file: ", err)
	}
}

func add_data(data_file_path string, job_data map[string]interface{}, jsonData map[string]interface{}) map[string]interface{} {
	// json encode jsonData and append to file data_file_path
	json_data, err := json.Marshal(jsonData)
	if err != nil {
		log.Fatal("Cannot marshal data: ", err)
	}
	f, err := os.OpenFile(data_file_path, os.O_APPEND|os.O_WRONLY, 0600)
	if err != nil {
		log.Fatal("Cannot open file: ", err)
	}
	defer f.Close()
	_, err = f.WriteString(string(json_data) + "\n")
	if err != nil {
		log.Fatal("Cannot write to file: ", err)
	}

	// update the running dict
	job_id := jsonData["job_id"].(string)
	if _, ok := job_data[job_id]; !ok {
		// create a list and fill it with jsonData
		job_data[job_id] = []interface{}{jsonData}
	} else {
		job_data[job_id] = append(job_data[job_id].([]interface{}), jsonData)
	}
	return job_data
}

func main() {
	fmt.Println("Starting server on port 8989")

	data_file_path := "./_data/all_data.jsonl"
	job_data_list, job_data := get_data(data_file_path)

	r := gin.Default()
	r.LoadHTMLGlob("static/*")

	// basic '/ping' route that returns the server time
	r.GET("/", func(c *gin.Context) {
		c.HTML(http.StatusOK, "index.html", gin.H{
			"server_time": time.Now().String(),
		})
	})

	r.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"time": time.Now().String(),
		})
	})

	// POST /log to record the job data in json
	r.POST("/log", func(c *gin.Context) {
		// // get the json data from the request
		var jsonData map[string]interface{}

		buf, e := ioutil.ReadAll(c.Request.Body)
		if e != nil {
			fmt.Println(e)
		}
		json.Unmarshal(buf, &jsonData)

		// user bad data error handling
		if len(jsonData) == 0 {
			c.JSON(http.StatusBadRequest, gin.H{
				"message": "No data received or invalid data, please check!",
			})
		}

		if jsonData["job_id"] == nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"message": "No job_id received, please check!",
			})
		}
		if jsonData["time"] == nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"message": "No timestamp received, please check!",
			})
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "Data received!",
		})

		// update job data for this job id\
		add_data(data_file_path, job_data, jsonData)

	})

	r.GET("/get_job_ids", func(c *gin.Context) {
		// return all the job ids
		job_ids := make([]string, 0, len(job_data))
		for k := range job_data {
			job_ids = append(job_ids, k)
		}
		c.JSON(http.StatusOK, gin.H{
			"job_ids": job_ids,
		})
	})

	// now the final route to get the data for a job id
	r.GET("/get_data/:job_id", func(c *gin.Context) {
		// get the job id from the request
		job_id := c.Param("job_id")
		data := job_data[job_id]

		c.JSON(http.StatusOK, gin.H{"data": data})

	})

	r.GET("/random_data", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"data": []float64{rand.Float64(), rand.Float64()},
		})
	})

	r.Run(":8989")

	// now support keyboard interrupt
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)

	go func() {
		<-c
		cleanup(job_data_list, data_file_path)
		os.Exit(1)
	}()
}
