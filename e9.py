import streamlit as st
from diagrams import Diagram
import google.generativeai as genai
import os
import yaml


class Diagrams:
    def __init__(self, name, prompt):
        self.prompt = prompt
        self.c_string = ""
        self.f_line = f'with Diagram("{name}", show=False):\n'
        global aws
        global data

    @staticmethod
    def get_data():
        # Load architecture description from YAML file
        with open("./aws.yaml", "r") as file:
            aws = yaml.safe_load(file)

        with open("./data.yaml", "r") as file:
            data = yaml.safe_load(file)

        with open("./connections.yaml", "r") as file:
            con = yaml.safe_load(file)

        return aws, data, con
    
    def dia(self):
        aws, data, con = self.get_data()
        self.c_string += "from diagrams import Cluster,Diagram\n"
        # imports
        components = data.keys()
        aws_lower_to_org = {k.lower(): k for k in aws.keys()}
        for k in components:
            k_lower = k.lower()
            if k_lower in aws_lower_to_org:
                org_key = aws_lower_to_org[k_lower]
                statement = f'from {aws[org_key]} import {org_key}\n'
                self.c_string += statement
            else:
                print(f'{k} not found')
        self.c_string += self.f_line
        # components
        for k, v in data.items():
            k_lower=k.lower()
            org_key = aws_lower_to_org[k_lower]
            if v == 1:
                self.c_string += f'    {k_lower} = {org_key}("{k_lower}")\n'
            else:
                arr = []
                for i in range(v):
                    str_component = f'{org_key}("{k_lower}-{i+1}")'
                    arr.append(str_component)
                arr_str = "[" + ", ".join(arr) + "]"
                cluster = f'    with Cluster("{k_lower}"):\n'
                self.c_string+=cluster
                self.c_string += f'        {k_lower} = {arr_str}\n'
        # connections
        for f, t in con.items():
            self.c_string += f'    {f.lower()} >> {t.lower()}\n'
        
        return self.c_string
    
    def execute(self):
        if not self.prompt:
            return "Error: Prompt is empty. Please provide a valid prompt."

        self.format_data()
        self.format_con()

        generated_code = self.dia()
        print(generated_code)
        exec(generated_code)
        st.image('cloud_architecture.png')
        return generated_code
        
    
    def gemini(self):
        genai.configure(api_key=os.environ.get('gemini_api'))
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt_data = self.prompt+" for this cloud architecture data give output in yaml format consisting of aws service names and the number of instances of each as key value pairs. No need for explaination just give the yaml data. the output should be aws_servise:number_of_instances. do not include yaml term in response. The aws service names should be in single word popular short terms, mostly capital unless popular terms have 1st letter capital and other small like Route53"
        prompt_con = self.prompt+"for this cloud architecture data give yaml data to tell which aws service is connected to which. give code in format from_aws_servise: to_aws_servise, where from_aws_servise is the key and to_aws_servise is value. No explanation required give only yaml data.  The aws service names should be in single word, all capital and in popular short terms.The aws service names should be in single word popular short terms, mostly capital unless popular terms have 1st letter capital and other small like Route53"

        res_data = model.generate_content(prompt_data).text
        res_con = model.generate_content(prompt_con).text

        return res_data,res_con

    def format_data(self):
        res_data,res_con = self.gemini()
        self.str_yaml(res_data,'data.yaml')
        # self.str_yaml(res_con,'connections.yaml')

    def format_con(self):
        res_data,res_con = self.gemini()
        # self.str_yaml(res_data,'data.yaml')
        self.str_yaml(res_con,'connections.yaml')


    def str_yaml(self,res,file_path):
        res = str(res).replace("yaml", "")
        # st.write(res)
        lines = res.strip().split('\n')
        data = {}
        for line in lines:
            # st.write(line)
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                try:
                    value = int(value)
                except ValueError:
                    pass
                data[key] = value
        data.pop('aws_service', None)
        data.pop('connections', None)

        with open(file_path, "w") as file:
            yaml.dump(data, file, default_flow_style=False)


def main():
    st.title("Cloud Architecture Diagram Generator")
    prompt = st.text_input("Enter the cloud architecture")

    if prompt:
        obj = Diagrams("Cloud Architecture", prompt)
        res = obj.execute()
        st.write(res)
    else:
        st.write("Please provide a prompt to generate the cloud architecture diagram.")


    # prompt = st.text_input("Enter the cloud architecture")
    # prompt = "consider the data this architecture efficiently manages web traffic, processes application tasks, and maintains data in a centralized and managed database, ensuring high performance and reliability.Traffic flows from the ELB to the 3 EC2 worker instances, which then interact with the RDS database. for this cloud architecture data give output in yaml format consisting of aws service names and the number of instances of each as key value pairs. No need for explaination just give the yaml data. the output should be aws_servise:number_of_instances. do not include yaml term in response"
    # obj = Diagrams("Cloud Architecture", prompt)
    # obj.str_yaml()


if __name__ == "__main__":
    main()
